# PySide6 GUI 整体架构

> Python ↔ QML 桥接模式、模块职责、依赖关系、Context Property 注册顺序。

## 技术栈与依赖

| 层次 | 技术 | 用途 |
|------|------|------|
| GUI 框架 | PySide6 (Qt 6) | QApplication, QQmlApplicationEngine, QObject |
| 声明式 UI | QML (QtQuick 2.15) | 页面布局、组件、动画 |
| 控件风格 | QtQuick.Controls "Basic" | 自定义外观（TextField, RadioButton 等） |
| 系统对话框 | Qt.labs.platform 1.1 | FolderDialog 目录选择 |
| 图像处理 | QQuickImageProvider | 将 QStyle 标准图标暴露给 QML |
| 并发 | threading + QMutex | 后台执行 CoreEngine，不阻塞 UI |
| 核心引擎 | core (avdc-core) | 纯业务逻辑，零 Qt 依赖 |

## 文件索引

### Python 侧（`pyside6_gui/`）

| 文件 | 职责 |
|------|------|
| `main.py` | 入口。创建 QApplication/Engine、注册 Context Properties、Theme 常量、IconProvider、WindowController |
| `settings_model.py` | 配置模型。SCHEMA 驱动，类工厂自动生成 38 个 Qt Property，load/save/resetToDefaults |
| `processing_model.py` | 处理模型。CoreEngine 的 QML 包装器，后台线程执行，Signal 报告进度 |
| `log_model.py` | 日志模型。LogListModel (QAbstractListModel) + LogFilterModel（级别过滤） |
| `log_bridge.py` | 日志桥接。EventBus → Qt Signal 适配器 |

### QML 侧（`pyside6_gui/qml/`）

| 文件 | 职责 |
|------|------|
| `main.qml` | ApplicationWindow。TitleBar + SplitView + Sidebar + Loader + Toast + ResizeHandles + Shortcuts |
| `MacOSSidebar.qml` | 侧边栏导航。5 个导航项，选中指示器，可折叠 |
| `HomePage.qml` | 主页/工作台。文件选择、模式切换、开始/停止、进度显示 |
| `LogPage.qml` | 日志页。过滤栏 + LogViewer |
| `SettingsPage.qml` | 设置页。分组 SectionCard 包裹 Config* 组件 |
| `ToolsPage.qml` | 工具页。GridLayout 展示 ToolCard |
| `AboutPage.qml` | 关于页。版本信息、依赖列表 |

### 组件（`pyside6_gui/qml/components/`）

| 文件 | 职责 |
|------|------|
| `SectionCard.qml` | 分组容器（标题 + 分割线 + 子内容） |
| `ConfigInput.qml` | 标签 + 文本输入框 |
| `ConfigFilePicker.qml` | 标签 + 文本框 + 浏览按钮 |
| `ConfigRadioGroup.qml` | 标签 + 水平单选按钮组 |
| `ConfigSwitch.qml` | 标签 + 开关（bool） |
| `ConfigSwitchInt.qml` | 标签 + 开关（int 0/1） |
| `ConfigSlider.qml` | 标签 + 滑块 + 数值显示 |
| `ConfigCheckbox.qml` | 标签 + 复选框 |
| `TitleBar.qml` | 自定义标题栏（拖拽 + 窗口控制按钮） |
| `TitleBarButton.qml` | 单个窗口控制按钮 |
| `ResizeHandle.qml` | 边缘拖拽调整窗口大小 |
| `ProgressBar.qml` | 进度条 + 百分比 + 状态文字 |
| `LogViewer.qml` | 虚拟化日志列表（ListView + QAbstractListModel） |
| `ToolCard.qml` | 工具卡片（标题 + 描述 + 操作按钮） |
| `StatusBadge.qml` | 状态徽章（success/error/warning/info） |

## 数据流架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Python 侧                                │
│                                                                 │
│  config.ini ──→ AppConfig.from_ini() ──→ SettingsModel          │
│                                            │                    │
│  CoreEngine ←── settings.to_app_config() ←─┘                    │
│       │                                                         │
│       ├── on_log ──→ EventBus ──→ LogBridge ──→ LogFilterModel  │
│       ├── on_progress ──→ ProcessingModel.progressValue          │
│       ├── on_success ──→ ProcessingModel.successCount            │
│       └── on_failure ──→ ProcessingModel.failCount               │
│                                                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │ setContextProperty()
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        QML 侧                                   │
│                                                                 │
│  settings.xxx  ←──→  ConfigInput/ConfigSwitch/... (双向绑定)     │
│  processing.progressValue ──→ ProgressBar (只读)                 │
│  logModel.filteredModel ──→ LogViewer.ListView (虚拟化)          │
│  Theme.xxx ──→ 所有组件 (只读)                                   │
│  windowController ──→ TitleBar 按钮 (Slot 调用)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Context Property 注册顺序

`main.py` 中的注册顺序有依赖关系，不可打乱：

```python
# 1. Theme 常量（只读，所有组件依赖）
engine.rootContext().setContextProperty("Theme", THEME)

# 2. SettingsModel（配置绑定，HomePage/SettingsPage 依赖）
settings = SettingsModel()
engine.rootContext().setContextProperty("settings", settings)

# 3. Log 系统（EventBus → LogBridge → LogFilterModel）
event_bus = EventBus()
log_model = LogFilterModel(max_entries=1000)
log_bridge = LogBridge(event_bus=event_bus)
log_bridge.connect()
log_bridge.logReceived.connect(log_model.addEntry)
engine.rootContext().setContextProperty("logModel", log_model)

# 4. ProcessingModel（依赖 settings）
processing = ProcessingModel(config_model=settings)
engine.rootContext().setContextProperty("processing", processing)

# 5. WindowController（必须在 engine.load() 之前注册）
controller = WindowController()
engine.rootContext().setContextProperty("windowController", controller)

# 6. 加载 QML
engine.load(qml_file)

# 7. 设置无边框窗口 + 连接 WindowController
window = engine.rootObjects()[0]
window.setFlags(Qt.FramelessWindowHint | ...)
controller.set_window(window)
```

## 启动时序图

`main()` 函数的完整执行流程：

```
main()
│
├─ 1. sys.path 注入项目根目录（确保 core 包可导入）
├─ 2. QT_QUICK_CONTROLS_STYLE = "Basic"（允许自定义 TextField/RadioButton 外观）
├─ 3. QApplication(sys.argv) + setOrganizationName/setApplicationName
├─ 4. QQmlApplicationEngine()
├─ 5. IconProvider(app) → engine.addImageProvider("styleicons", ...)
│      将 QStyle 标准图标（house/doc/wrench/gear/info/expand/collapse）暴露给 QML
├─ 6. SettingsModel() → setContextProperty("settings", ...)
│      内部: AppConfig.from_ini() → 填充 _fields → Property getter 可用
├─ 7. setContextProperty("Theme", THEME)  — 纯 dict，无副作用
├─ 8. EventBus() + LogFilterModel(1000) + LogBridge(event_bus)
│      log_bridge.connect()  — 订阅 LOG_INFO/LOG_ERROR/LOG_SEPARATOR
│      log_bridge.logReceived.connect(log_model.addEntry)
│      → setContextProperty("logModel", ...)
├─ 9. ProcessingModel(config_model=settings) → setContextProperty("processing", ...)
│      注意：config_model 是 SettingsModel 实例，用于 to_app_config()
├─ 10. WindowController() → setContextProperty("windowController", ...)
│       此时 _win = None，等 QML 加载完成后通过 set_window() 注入
├─ 11. engine.load(qml_file)
│       QML 解析 → 实例化 main.qml → Component.onCompleted → 首页加载
├─ 12. window = engine.rootObjects()[0]
│       window.setFlags(FramelessWindowHint | WindowSystemMenuHint | ...)
│       window.setColor(Qt.transparent)  — 启用像素级透明，圆角平滑
│       controller.set_window(window)  — 连接 visibilityChanged 信号
└─ 13. app.exec()  — 进入 Qt 事件循环
```

## main.py 启动流程详解

### sys.path 注入

```python
# main.py 第 6-10 行
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
```

**原因**：`pyside6_gui/` 作为独立包运行，需要向上查找 `core/` 包。不使用 `pip install -e .` 时必须手动注入。

### QT_QUICK_CONTROLS_STYLE

```python
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
```

**原因**：默认 macOS 风格会锁定 TextField/RadioButton 外观，无法自定义背景和边框。Basic 风格允许完全覆盖。

### IconProvider 实现

```python
class IconProvider(QQuickImageProvider):
    def __init__(self, app):
        super().__init__(QQuickImageProvider.Image)
        self._style_map = {
            "house": QStyle.SP_DirHomeIcon,
            "doc": QStyle.SP_FileIcon,
            "wrench": QStyle.SP_DialogApplyButton,
            "gear": QStyle.SP_DialogHelpButton,
            "info": QStyle.SP_MessageBoxInformation,
            "expand": QStyle.SP_ArrowRight,
            "collapse": QStyle.SP_ArrowLeft,
        }

    def requestImage(self, id, size, requestedSize):
        m = re.match(r"^(house|doc|wrench|gear|info|expand|collapse)", id)
        if not m:
            return QImage()
        sp = self._style_map.get(m.group(1))
        icon = self._app.style().standardIcon(QStyle.StandardPixmap(sp))
        w = requestedSize.width() if requestedSize is not None else 16
        h = requestedSize.height() if requestedSize is not None else 16
        return icon.pixmap(w, h).toImage()
```

QML 使用：`source: "image://styleicons/house"`

### WindowController 内联定义

`main.py` 将 `WindowController` 定义在 `main()` 函数内部（非顶层类），因为它只在启动时用到一次：

```python
def main():
    # ...

    class WindowController(QObject):
        isMaximizedChanged = Signal()

        def __init__(self):
            super().__init__()
            self._win = None  # 延迟注入

        def set_window(self, win: QQuickWindow):
            self._win = win
            self._win.visibilityChanged.connect(self._on_visibility_changed)

        @Slot()
        def startMove(self):
            if self._win:
                self._win.startSystemMove()

        @Slot(int)
        def startResize(self, edge: int):
            if self._win:
                self._win.startSystemResize(Qt.Edge(edge))

        @Slot()
        def minimize(self):
            if self._win:
                self._win.showMinimized()

        @Slot()
        def maximize(self):
            if self._win:
                if self._win.visibility() == QQuickWindow.Maximized:
                    self._win.showNormal()
                else:
                    self._win.showMaximized()

        @Slot()
        def closeWindow(self):
            if self._win:
                self._win.close()

        @Property(bool, notify=isMaximizedChanged)
        def isMaximized(self):
            if self._win:
                return self._win.visibility() == QQuickWindow.Maximized
            return False

    controller = WindowController()
    engine.rootContext().setContextProperty("windowController", controller)
```

### 窗口标志设置（加载后）

必须在 `engine.load()` **之后**，因为此时才能获取 root window 对象：

```python
window = engine.rootObjects()[0]
if isinstance(window, QQuickWindow):
    window.setFlags(
        Qt.FramelessWindowHint        # 移除系统标题栏
        | Qt.WindowSystemMenuHint     # 保留系统菜单（Alt+Space）
        | Qt.WindowMinMaxButtonsHint  # 保留最小/最大按钮语义
    )
    window.setColor(Qt.transparent)   # 启用像素级透明，圆角平滑
    controller.set_window(window)     # 注入窗口引用
```

## 页面加载机制

使用 `Loader` + `Component` 实现懒加载，切换页面时才实例化：

```qml
// main.qml
Component { id: homePageComponent; HomePage {} }
Component { id: logPageComponent; LogPage {} }
// ... 5 个页面

Loader {
    id: pageLoader
    property int currentPage: 0
    property var _components: [homePageComponent, logPageComponent, ...]
    onCurrentPageChanged: sourceComponent = _components[currentPage]
}

// MacOSSidebar 点击触发
onItemClicked: function(index) {
    pageLoader.currentPage = index
}
```

**优点**：初始只加载首页，其余页面按需创建，减少启动时间。

## IconProvider

将 Qt 系统图标暴露给 QML，避免自定义图标资源：

```python
class IconProvider(QQuickImageProvider):
    def requestImage(self, id, size, requestedSize):
        # id 匹配: "house", "doc", "wrench", "gear", "info", "expand", "collapse"
        sp = self._style_map.get(id)
        return app.style().standardIcon(sp).pixmap(w, h).toImage()
```

QML 使用：`source: "image://styleIcons/house"`
