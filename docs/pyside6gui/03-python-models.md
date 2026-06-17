# Python 模型层

> SettingsModel、ProcessingModel、Log 系统的实现细节与数据流。

## 1. SettingsModel — 配置绑定

**文件**：`pyside6_gui/settings_model.py`

### SCHEMA 驱动设计

所有 `config.ini` 字段在一个 dict 中声明，自动生成 Qt Property：

```python
SCHEMA: dict[str, tuple[type, object, str]] = {
    # config_key:    (Python类型, 默认值,     QML属性名)
    "main_mode":    (int,  1,                          "mainMode"),
    "soft_link":    (int,  0,                          "softLink"),
    "proxy":        (str,  "",                         "proxy"),
    "timeout":      (int,  7,                          "timeout"),
    # ... 共 38 个字段
}
```

### 类工厂模式

由于 PySide6 的 Property 必须在类创建时注册到 meta-object（详见 07-dynamic-property），使用工厂函数动态构建类：

```python
def _create_settings_model_class() -> type:
    namespace = {
        '__module__': __name__,
        'configLoaded': Signal(),
        'configSaved': Signal(),
        'errorOccurred': Signal(str),
    }

    for config_key, (type_, default, qml_name) in SCHEMA.items():
        signal_name = f"{qml_name}Changed"
        namespace[signal_name] = Signal(type_)

        getter = make_getter(config_key)   # 闭包捕获 key
        setter = make_setter(config_key, signal_name)
        namespace[qml_name] = Property(type_, getter, setter, notify=namespace[signal_name])

    # 添加方法
    namespace['__init__'] = __init__
    namespace['load'] = load
    namespace['save'] = save
    namespace['resetToDefaults'] = resetToDefaults
    namespace['to_app_config'] = to_app_config

    return type('SettingsModel', (QObject,), namespace)

SettingsModel = _create_settings_model_class()
```

### 内部存储

所有字段值存储在 `self._fields: dict` 中，getter/setter 通过闭包访问：

```python
def make_getter(key):
    def getter(self):
        return self._fields.get(key)
    return getter

def make_setter(key, sig):
    def setter(self, value):
        if self._fields.get(key) != value:
            self._fields[key] = value
            getattr(self, sig).emit(value)  # 通知 QML
    return setter
```

### 核心方法

| 方法 | 说明 |
|------|------|
| `load()` | 从 `config.ini` 读取 → `AppConfig.from_ini()` → 填充 `_fields` |
| `save()` | `_fields` → `AppConfig(**fields)` → `to_ini()` 写入磁盘 |
| `resetToDefaults()` | 重置 `_fields` 为 SCHEMA 默认值 |
| `to_app_config()` | 创建 `AppConfig` 实例，供 CoreEngine 使用 |
| `get(key)` / `set(key, value)` | 泛型访问器，QML 可通过 `settings.get('main_mode')` 调用 |

### QML 双向绑定

```qml
ConfigInput {
    labelText: "代理地址"
    textValue: settings.proxy              // 读取
    onTextValueChanged: settings.proxy = textValue  // 写入
}
```

---

## 2. ProcessingModel — 处理引擎

**文件**：`pyside6_gui/processing_model.py`

### 职责

将 `CoreEngine` 包装为 QObject，在后台线程执行，通过 Signal 报告进度。

### 信号定义

```python
class ProcessingModel(QObject):
    # 状态
    isProcessingChanged = Signal(bool)

    # 进度
    progressChanged = Signal(float)           # 0.0 - 1.0
    batchProgress = Signal(int, int)          # current, total
    processingFinished = Signal(int, int, int)  # success, fail, skip

    # 事件
    logMessage = Signal(str, str)             # level, message
    movieProcessed = Signal(str, bool)        # number, success

    # QML 绑定属性
    progressValueChanged = Signal(float)
    statusTextChanged = Signal(str)
    successCountChanged = Signal(int)
    failCountChanged = Signal(int)
    skipCountChanged = Signal(int)
```

### 线程模型

```
┌─────────────┐                    ┌───────────────┐
│   Main UI    │                    │  Worker Thread │
│  (Qt Event   │                    │  (daemon)      │
│   Loop)      │                    │                │
│              │  start_batch() ──→ │ CoreEngine     │
│              │                    │  .process_batch│
│  ← progress  │  ← batchProgress  │     ()         │
│  ← counts    │  ← logMessage     │                │
│              │                    │ 完成 ──────────│
│  _finishProc │  invokeMethod()   │                │
│  (主线程)     │                    │                │
└─────────────┘                    └───────────────┘
```

**关键点**：
- Worker 线程通过回调（`on_log`, `on_progress` 等）发射 Qt Signal
- 完成后通过 `QMetaObject.invokeMethod(self, "_finishProcessing", Qt.QueuedConnection)` 回到主线程恢复状态
- 使用 `QMutex` 保护 `_stop_requested` 标志

### 回调桥接

```python
def on_progress(current, total, filepath):
    self.batchProgress.emit(current, total)
    self._emit_progress(current / total)
    self._emit_log("INFO", f"[{current}/{total}] {os.path.basename(filepath)}")

def on_success(filepath, suffix):
    number = getNumber(filepath, "") or filepath
    self.movieProcessed.emit(number, True)
```

### QML 使用

```qml
// 启动
Button {
    onClicked: processing.start_batch(
        settings.mediaPath,
        settings.escapeFolders,
        settings.mainMode
    )
}

// 监听进度
Connections {
    target: processing
    function onProgressChanged(value) { progressBar.progressValue = value }
    function onProcessingFinished(s, f, sk) { /* 更新统计 */ }
}
```

---

## 3. Log 系统 — 全链路

**文件**：`log_bridge.py` → `log_model.py` → `LogViewer.qml`

### 数据流

```
core.EventBus
    │ emit(EventType.LOG_INFO / LOG_ERROR / LOG_SEPARATOR)
    ▼
LogBridge（适配器）
    │ logReceived.emit(level, message)  — Qt Signal
    ▼
LogFilterModel
    │ addEntry(level, message)
    │ ├── 统一级别名称（ERR→ERROR, WARNING→WARN）
    │ ├── 生成时间戳 (HH:mm:ss)
    │ ├── 添加到 source_model (LogListModel)
    │ └── 如果匹配过滤条件 → 添加到 filtered_model
    ▼
LogViewer.qml (ListView)
    │ model: logModel.filteredModel
    │ 只渲染可见行（虚拟化）
    ▼
QML 显示
```

### LogBridge — EventBus 适配器

```python
class LogBridge(QObject):
    logReceived = Signal(str, str)

    def connect(self):
        self._handlers[EventType.LOG_INFO] = self._on_log_info
        self._handlers[EventType.LOG_ERROR] = self._on_log_error
        self._handlers[EventType.LOG_SEPARATOR] = self._on_log_separator
        for event_type, handler in self._handlers.items():
            self._event_bus.on(event_type, handler)
```

### LogListModel — QAbstractListModel

实现 Qt Model/View 虚拟化，ListView 只为可见行请求 `data()`：

```python
class LogListModel(QAbstractListModel):
    LevelRole = Qt.UserRole + 1
    MessageRole = Qt.UserRole + 2
    TimestampRole = Qt.UserRole + 3

    def rowCount(self, parent): return len(self._entries)

    def data(self, index, role):
        entry = self._entries[index.row()]
        if role == self.LevelRole: return entry.level
        if role == self.MessageRole: return entry.message
        if role == self.TimestampRole: return entry.timestamp

    def append(self, entry):
        row = len(self._entries)
        self.beginInsertRows(QModelIndex(), row, row)
        self._entries.append(entry)
        self.endInsertRows()
        # 超出 max_entries 时删除最旧的
        excess = len(self._entries) - self._max_entries
        if excess > 0:
            self.beginRemoveRows(QModelIndex(), 0, excess - 1)
            self._entries = self._entries[excess:]
            self.endRemoveRows()
```

### LogFilterModel — 级别过滤

```python
LEVEL_PRIORITY = {'ERROR': 0, 'WARN': 1, 'INFO': 2, 'DEBUG': 3}

# 过滤逻辑：
# "error" → 只显示 ERROR
# "warn"  → 显示 ERROR + WARN
# "info"  → 显示 ERROR + WARN + INFO
# "debug" → 显示全部
# "all"   → 显示全部
```

维护两个 `LogListModel`：
- `_source_model`：完整日志（不受过滤影响）
- `_filtered_model`：过滤后的日志（QML 绑定这个）

切换 `filterLevel` 时调用 `_rebuild_filtered_model()` 重建。

### LogViewer.qml — 虚拟化渲染

```qml
ListView {
    model: logModel.filteredModel
    cacheBuffer: 100  // 缓存额外 100px，平滑滚动

    delegate: RowLayout {
        Text { text: model.timestamp }           // 时间戳
        Rectangle { Text { text: model.level } } // 级别徽章
        Text { text: model.message }             // 日志内容
    }

    // 自动滚动到底部
    onCountChanged: {
        if (count > 0 && !atYEnd) autoScrollTimer.start()
    }
}
```
