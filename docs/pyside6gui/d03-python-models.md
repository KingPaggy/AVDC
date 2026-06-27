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

---

## 4. EventBus 集成

### 架构概览

```
CoreEngine (core 层)
    ↓ on_log 回调
EventBus.emit(LOG_INFO / LOG_ERROR)
    ↓
LogBridge._on_log_info(event)
    ↓ logReceived.emit("INFO", message)
LogFilterModel.addEntry(level, message)
    ↓ QAbstractListModel
LogViewer.qml (ListView)
```

### LogBridge 订阅逻辑

```python
# pyside6_gui/log_bridge.py
class LogBridge(QObject):
    logReceived = Signal(str, str)  # (level, message)

    def connect(self):
        """订阅 EventBus 日志事件"""
        self._handlers[EventType.LOG_INFO] = self._on_log_info
        self._handlers[EventType.LOG_ERROR] = self._on_log_error
        self._handlers[EventType.LOG_SEPARATOR] = self._on_log_separator

        for event_type, handler in self._handlers.items():
            self._event_bus.on(event_type, handler)

    def disconnect(self):
        """取消订阅"""
        for event_type, handler in self._handlers.items():
            self._event_bus.off(event_type, handler)
        self._handlers.clear()

    def _on_log_info(self, event):
        self.logReceived.emit("INFO", getattr(event, "message", ""))

    def _on_log_error(self, event):
        self.logReceived.emit("ERROR", getattr(event, "message", ""))

    def _on_log_separator(self, event):
        self.logReceived.emit("SEPARATOR", "---")
```

### 初始化顺序（main.py）

```python
# 1. 创建 EventBus
event_bus = EventBus()

# 2. 创建 LogFilterModel
log_model = LogFilterModel(max_entries=1000)

# 3. 创建 LogBridge 并订阅
log_bridge = LogBridge(event_bus=event_bus)
log_bridge.connect()

# 4. 连接 LogBridge 信号到 LogFilterModel
log_bridge.logReceived.connect(log_model.addEntry)

# 5. 注入 QML Context
engine.rootContext().setContextProperty("logModel", log_model)
```

### 生命周期管理

```python
# 应用退出时清理
def cleanup():
    log_bridge.disconnect()  # 避免悬挂引用
```

---

## 5. ProcessingModel 线程模型

### 回调桥接

ProcessingModel 将 CoreEngine 的回调转换为 Qt Signal：

```python
class ProcessingModel(QObject):
    @Slot(str, str, int)
    def start_batch(self, movie_path, escape_folder, scraper_mode):
        # 创建回调函数（在 Worker 线程中调用）
        def on_progress(current, total, filepath):
            self.batchProgress.emit(current, total)
            self._emit_progress(current / total)

        def on_success(filepath, suffix):
            self.movieProcessed.emit(number, True)

        def on_failure(filepath, reason, error):
            self.movieProcessed.emit(number, False)
            self._emit_log("ERROR", f"失败: {filepath}")

        # Worker 线程
        def _worker():
            cfg = self._config_model.to_app_config()
            engine = CoreEngine(
                config=cfg,
                on_log=on_log,
                on_progress=on_progress,
                on_success=on_success,
                on_failure=on_failure,
            )
            result = engine.process_batch(movie_path, escape_folder, scraper_mode)

            # 完成后回到主线程
            QMetaObject.invokeMethod(
                self, "_finishProcessing",
                Qt.ConnectionType.QueuedConnection
            )

        self._worker_thread = threading.Thread(target=_worker, daemon=True)
        self._worker_thread.start()
```

### 线程安全

```python
# 使用 QMutex 保护停止标志
from PySide6.QtCore import QMutex, QMutexLocker

class ProcessingModel(QObject):
    def __init__(self):
        self._stop_requested = False
        self._mutex = QMutex()

    @Slot()
    def stop(self):
        with QMutexLocker(self._mutex):
            self._stop_requested = True

    @property
    def _should_stop(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._stop_requested
```

---

## 6. 配置持久化

### config.ini 结构

```ini
[common]
main_mode = 1
soft_link = 0
success_output_folder = JAV_output

[proxy]
proxy_type = http
proxy = 127.0.0.1:7890
timeout = 10
retry = 3
```

### load() 实现

```python
@Slot()
def load(self):
    """从 config.ini 加载配置"""
    try:
        cfg = AppConfig.from_ini(self._config_path)
        for config_key in SCHEMA:
            self._fields[config_key] = getattr(cfg, config_key)
        self.configLoaded.emit()
    except Exception as e:
        self.errorOccurred.emit(f"加载配置失败: {e}")
```

### save() 实现

```python
@Slot()
def save(self):
    """保存配置到 config.ini"""
    try:
        cfg = AppConfig(**self._fields)
        cfg.to_ini(self._config_path)
        self.configSaved.emit()
    except Exception as e:
        self.errorOccurred.emit(f"保存配置失败: {e}")
```

---

## 7. 错误处理模式

### Python 侧异常捕获

```python
@Slot()
def load(self):
    try:
        cfg = AppConfig.from_ini(self._config_path)
        # ...
    except FileNotFoundError as e:
        self.errorOccurred.emit(f"配置文件不存在: {e}")
    except Exception as e:
        self.errorOccurred.emit(f"未知错误: {e}")
```

### QML 侧错误显示

```qml
Connections {
    target: settings
    function onErrorOccurred(message) {
        toast.show(message, "error")
    }
}
```

---

## 8. 最佳实践

### 1. 使用 SCHEMA 驱动 Property 生成

避免手动定义 38 个 Property，使用类工厂自动生成。

### 2. 始终发射 notify Signal

setter 修改内部状态后必须发射对应的 Signal，否则 QML 不会更新。

### 3. 跨线程使用 QueuedConnection

Worker 线程不能直接修改 QML 绑定的 Property，必须通过 `QMetaObject.invokeMethod` 回到主线程。

### 4. 使用 QMutex 保护共享状态

停止标志等跨线程状态必须用 QMutex 保护，避免竞态条件。

### 5. 分离源模型和过滤模型

日志系统使用双模型设计，避免频繁重建过滤列表。

### 6. 错误通过 Signal 报告

不要在 Python 侧捕获异常后静默，通过 `errorOccurred` Signal 报告给 QML 显示。
