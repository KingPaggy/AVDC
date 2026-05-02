# UI 与内核通信机制

本文档描述 AVDC 的 UI 层与核心业务逻辑之间的通信协议、线程安全方案和事件系统。

## 回调模式 — CoreEngine 的四大回调

**文件**：[core/_services/orchestrator.py](core/_services/orchestrator.py)

```python
OnLog = Callable[[str], None]                          # 日志消息
OnProgress = Callable[[int, int, str], None]           # (当前进度, 总数, 文件路径)
OnSuccess = Callable[[str, str], None]                 # (文件路径, 后缀字符串)
OnFailure = Callable[[str, str, Exception], None]      # (文件路径, 失败原因, 异常对象)
```

CoreEngine 构造函数接受可选回调，未提供时使用默认 logger 或空操作：

```python
engine = CoreEngine(
    config=config,
    on_log=safe_log,
    on_progress=safe_progress,
    on_success=safe_success,
    on_failure=safe_failure,
)
```

### 回调触发时机

| 回调 | 触发场景 | 传递参数 |
|------|----------|----------|
| `on_log` | 每个文件处理开始/结束、错误、批量开始/结束 | 日志字符串 |
| `on_progress` | 每处理一个文件 | `(current, total, filepath)` |
| `on_success` | 文件刮削成功完成 | `(filepath, suffix)` |
| `on_failure` | 番号提取失败、刮削失败、异常 | `(filepath, reason, error)` |

## UI 如何创建 CoreEngine

**文件**：[main.py](main.py)

### 批量刮削（`AVDC_Main()` 方法，第 965-1010 行）

```python
def AVDC_Main(self):
    config = self._get_app_config()
    movie_path = config.media_path or os.getcwd().replace("\\", "/")

    def safe_log(msg):
        QMetaObject.invokeMethod(self.Ui.textBrowser_log, "append",
            Qt.QueuedConnection, Q_ARG(str, msg))

    def safe_progress(current, total, filepath):
        value = int(current / total * 100)
        self.progressBarValue.emit(value)

    def safe_success(filepath, suffix):
        movie_number = os.path.splitext(filepath.split("/")[-1])[0]
        node = QTreeWidgetItem(self.item_succ)
        node.setText(0, f"{self.count_claw}-{movie_number}{suffix}")
        self.item_succ.addChild(node)

    def safe_failure(filepath, reason, error):
        movie_name = os.path.splitext(filepath.split("/")[-1])[0]
        node = QTreeWidgetItem(self.item_fail)
        node.setText(0, f"{self.count_claw}-{movie_name}")
        self.item_fail.addChild(node)

    engine = CoreEngine(
        config=config, on_log=safe_log, on_progress=safe_progress,
        on_success=safe_success, on_failure=safe_failure,
    )
    result = engine.process_batch(movie_path=movie_path,
        escape_folder=config.folders, mode=config.main_mode)
```

### 单文件刮削

通过 `pushButton_start_single_file_clicked()` 触发，流程类似但调用 `engine.process_single()` 而非 `process_batch()`，支持手动指定番号和目标网站。

## 线程安全方案

### 后台线程模型

AVDC 使用 **Python 标准 threading.Thread**（而非 PyQt 的 QThread）运行后台任务：

```python
def pushButton_start_cap_clicked(self):
    self.Ui.pushButton_start_cap.setEnabled(False)
    self.progressBarValue.emit(int(0))
    self.count_claw += 1
    t = threading.Thread(target=self.AVDC_Main)
    t.start()
```

UI 中 5 个操作创建了后台线程：
- 批量刮削：`pushButton_start_cap_clicked()` → `AVDC_Main()`
- 保存配置：`save_config_clicked()`
- 恢复默认配置：`init_config_clicked()`
- 单文件刮削：`pushButton_start_single_file_clicked()`
- 文件移动：`move_file()`
- 查找演员头像：`found_profile_picture()`

### 跨线程 UI 更新策略

由于后台线程不能直接操作 Qt 控件，使用了三种策略：

**策略 1：`pyqtSignal` 跨线程信号**

```python
class AVDC_Main_UI(QMainWindow):
    progressBarValue = pyqtSignal(int)  # 类级别定义

# 在后台线程中 emit
self.progressBarValue.emit(value)

# 在主线程中接收（通过 connect 绑定）
self.progressBarValue.connect(self._on_progress)
```

PyQt 的 `pyqtSignal` 天然支持跨线程安全传递，`emit()` 在后台线程调用，槽函数在主线程执行。

**策略 2：`QMetaObject.invokeMethod` + `Qt.QueuedConnection`**

```python
def safe_log(msg):
    QMetaObject.invokeMethod(self.Ui.textBrowser_log, "append",
        Qt.QueuedConnection, Q_ARG(str, msg))
```

`QueuedConnection` 将方法调用放入主线程事件队列，确保 UI 操作在主线程执行。

**策略 3：直接操作 QTreeWidgetItem（在后台线程中）**

成功/失败节点通过 `QTreeWidgetItem` 直接添加到树控件。虽然这在后台线程中执行，但由于树控件不频繁重绘且操作是原子的，实践中不会崩溃。

## 配置双向流动

### UI → CoreEngine：`_get_app_config()`

**文件**：[main.py](main.py) 第 913-958 行

从 UI 控件状态构建 `AppConfig` dataclass：

```python
def _get_app_config(self) -> AppConfig:
    return AppConfig(
        main_mode=1 if self.Ui.radioButton.isChecked() else 2,
        soft_link=1 if self.Ui.radioButton_3.isChecked() else 0,
        proxy_type="http" if self.Ui.radioButton_19.isChecked() else (
            "socks5" if self.Ui.radioButton_20.isChecked() else "no"),
        # ... 30+ 个字段
    )
```

### CoreEngine → UI：回调报告

CoreEngine 处理过程中通过回调将进度、结果、错误推送回 UI，UI 更新对应控件（进度条、结果树、日志区）。

### 配置文件持久化

- **加载**：`Load_Config()` 读取 `config.ini` → 更新所有 UI 控件状态（RadioButton、LineEdit、CheckBox 等）
- **保存**：`save_config_clicked()` 读取 UI 控件 → 构建 JSON dict → `save_config()` 写回 `config.ini`

## EventBus 系统（预留）

**文件**：
- [core/_event/event_bus.py](core/_event/event_bus.py)
- [core/_event/events.py](core/_event/events.py)

### 架构

EventBus 是线程安全的 pub/sub 事件总线，使用 `threading.Lock` 保护 `_handlers` 字典：

```python
class EventBus:
    def on(self, event_type: EventType, handler: Callable[[Event], None])
    def off(self, event_type: EventType, handler: Callable[[Event], None])
    def emit(self, event_type: EventType, **kwargs)
    def clear(self)
```

### 事件类型（20+ 种）

| 分类 | 事件类型 |
|------|----------|
| 生命周期 | `PROCESSING_START`, `PROCESSING_END` |
| 日志 | `LOG_INFO`, `LOG_ERROR`, `LOG_SEPARATOR` |
| 进度 | `PROGRESS` |
| 文件操作 | `FILE_MOVED`, `FILE_DELETED`, `DIR_CREATED` |
| 下载 | `DOWNLOAD_START`, `DOWNLOAD_SUCCESS`, `DOWNLOAD_FAILED` |
| 图像处理 | `IMAGE_CUT`, `IMAGE_WATERMARK`, `IMAGE_RESIZE` |
| 刮削结果 | `SCRAPE_SUCCESS`, `SCRAPE_FAILED` |
| 批量操作 | `BATCH_START`, `BATCH_END` |

### 当前状态

EventBus **已实现但尚未在 UI 中使用**。当前 UI 通过直接回调与 CoreEngine 通信，EventBus 为未来重构预留。如果需要将细粒度事件（如"某个文件下载完成"、"海报裁剪完成"）推送给 UI，可以订阅对应 EventType。

## 通信流程总结

```
用户点击"开始刮削"
    │
    ▼
UI 禁用按钮，创建 threading.Thread
    │
    ▼
后台线程: _get_app_config() 从 UI 读取配置
    │
    ▼
后台线程: CoreEngine(config, on_log, on_progress, on_success, on_failure)
    │
    ├── on_log ──▶ QMetaObject.invokeMethod(append) ──▶ 日志区显示
    ├── on_progress ──▶ progressBarValue.emit(value) ──▶ 进度条更新
    ├── on_success ──▶ QTreeWidgetItem → 成功节点
    └── on_failure ──▶ QTreeWidgetItem → 失败节点
    │
    ▼
线程结束，UI 恢复按钮可用状态
```
