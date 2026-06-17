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
