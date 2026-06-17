# 窗口与导航

> 无边框窗口实现、TitleBar 拖拽、边缘调整大小、侧边栏导航、页面加载、Toast 通知。

## 1. 无边框窗口

### 实现方式

```python
# main.py — QML 加载后设置窗口标志
window = engine.rootObjects()[0]
window.setFlags(
    Qt.FramelessWindowHint        # 移除系统标题栏
    | Qt.WindowSystemMenuHint     # 保留系统菜单（Alt+Space）
    | Qt.WindowMinMaxButtonsHint  # 保留最小/最大按钮语义
)
window.setColor(Qt.transparent)   # 启用像素级透明，圆角平滑
```

### 圆角效果

通过两层 Rectangle 实现：

```qml
// main.qml
// 第 1 层：背景圆角裁剪
Rectangle {
    anchors.fill: parent
    color: Theme.backgroundColor
    radius: Theme.radiusXL   // 12px 圆角
    clip: true               // 裁剪子元素超出部分
}

// 第 2 层：内容容器
Item {
    id: roundedContainer
    anchors.fill: parent
    // TitleBar + SplitView + ...
}
```

**性能优化**：使用 `clip: true` + `radius` 而非 `OpacityMask`，避免 GPU 离屏渲染。

## 2. TitleBar

**文件**：`qml/components/TitleBar.qml`

### 结构

```
┌─────────────────────────────────────────────────┐
│ [◀]  AVDC                    [—]  [□]  [×]     │
│  ↑ sidebar                  ↑ minimize/maximize/close
│  toggle
└─────────────────────────────────────────────────┘
```

### 拖拽实现

TitleBar 底层是一个覆盖大部分区域的 MouseArea，手动计算窗口位移：

```qml
MouseArea {
    id: dragArea
    anchors.fill: parent
    anchors.rightMargin: buttonsRow.width + Theme.spacingSM

    onPressed: (mouse) => {
        var globalPos = dragArea.mapToGlobal(Qt.point(mouse.x, mouse.y))
        pressGlobalX = globalPos.x
        pressGlobalY = globalPos.y
        windowX = appWindow.x
        windowY = appWindow.y
    }

    onPositionChanged: (mouse) => {
        if (pressed) {
            var globalPos = dragArea.mapToGlobal(Qt.point(mouse.x, mouse.y))
            appWindow.x = windowX + (globalPos.x - pressGlobalX)
            appWindow.y = windowY + (globalPos.y - pressGlobalY)
        }
    }
}
```

**注意**：窗口控制按钮（`TitleBarButton`）位于拖拽区域上方（z 更高），点击按钮不会触发拖拽。

### WindowController

Python 侧的窗口控制桥，暴露给 QML 调用：

```python
class WindowController(QObject):
    isMaximizedChanged = Signal()

    @Slot()
    def startMove(self):        self._win.startSystemMove()

    @Slot(int)
    def startResize(self, edge): self._win.startSystemResize(Qt.Edge(edge))

    @Slot()
    def minimize(self):         self._win.showMinimized()

    @Slot()
    def maximize(self):
        if self._win.visibility() == QQuickWindow.Maximized:
            self._win.showNormal()
        else:
            self._win.showMaximized()

    @Slot()
    def closeWindow(self):      self._win.close()

    @Property(bool, notify=isMaximizedChanged)
    def isMaximized(self):
        return self._win.visibility() == QQuickWindow.Maximized
```

## 3. ResizeHandle — 边缘调整大小

**文件**：`qml/components/ResizeHandle.qml`

4 个边缘各一个不可见条带（8px），鼠标悬停时改变光标，按下时调用 `windowController.startResize(edge)`：

```qml
// main.qml 中放置 4 个 ResizeHandle
ResizeHandle { edge: Qt.TopEdge;    x: 8; y: 0; width: parent.width - 16; height: 8 }
ResizeHandle { edge: Qt.BottomEdge; x: 8; y: parent.height - 8; width: parent.width - 16; height: 8 }
ResizeHandle { edge: Qt.LeftEdge;   x: 0; y: 8; width: 8; height: parent.height - 16 }
ResizeHandle { edge: Qt.RightEdge;  x: parent.width - 8; y: 8; width: 8; height: parent.height - 16 }
```

角落由相邻两边重叠覆盖，无需单独处理。

光标形状根据 edge 自动切换：`SizeVerCursor` / `SizeHorCursor`。

## 4. MacOSSidebar — 侧边栏导航

**文件**：`qml/MacOSSidebar.qml`

### 导航项定义

```qml
readonly property var navItems: [
    { icon: "house.fill",                   label: "主页" },
    { icon: "doc.text.fill",                label: "日志" },
    { icon: "wrench.and.screwdriver.fill",   label: "工具" },
    { icon: "gearshape.fill",               label: "设置" },
    { icon: "info.circle.fill",             label: "关于" }
]
```

### 结构

```
┌──────────┐
│ 导航     │  ← section header (tertiaryText)
│          │
│ 🏠 主页  │  ← 选中态：accentColor 文字 + 左侧指示器
│ 📄 日志  │  ← 默认态：textColor 文字
│ 🔧 工具  │
│ ⚙️ 设置  │
│ ℹ️ 关于  │
│          │
│          │  ← Item { Layout.fillHeight: true } 底部弹性空间
└──────────┘
```

### 选中指示器

```qml
Rectangle {
    visible: root.currentIndex === index
    anchors.left: parent.left
    anchors.top: parent.top
    anchors.bottom: parent.bottom
    anchors.margins: Theme.spacingXS
    width: Theme.indicatorWidth   // 3px
    radius: Theme.radiusXS
    color: Theme.accentColor
}
```

### 折叠

```qml
// main.qml
property bool sidebarCollapsed: false

// 快捷键
Shortcut {
    sequences: ["Meta+Shift+S", "Ctrl+Shift+S"]
    onActivated: appWindow.sidebarCollapsed = !appWindow.sidebarCollapsed
}

// TitleBar 左侧按钮
TitleBarButton {
    icon: appWindow.sidebarCollapsed ? "expand" : "collapse"
    onClicked: appWindow.sidebarCollapsed = !appWindow.sidebarCollapsed
}
```

折叠时 `Layout.preferredWidth: 0` + `visible: false`。

## 5. Loader 懒加载

```qml
// 5 个 Component 声明
Component { id: homePageComponent; HomePage {} }
Component { id: logPageComponent; LogPage {} }
Component { id: toolsPageComponent; ToolsPage {} }
Component { id: settingsPageComponent; SettingsPage {} }
Component { id: aboutPageComponent; AboutPage {} }

Loader {
    id: pageLoader
    property int currentPage: 0
    property var _components: [
        homePageComponent, logPageComponent, toolsPageComponent,
        settingsPageComponent, aboutPageComponent
    ]
    onCurrentPageChanged: sourceComponent = _components[currentPage]
    Component.onCompleted: sourceComponent = _components[0]
}
```

切换页面时，`Loader` 销毁旧组件、实例化新组件。

## 6. Toast 通知

内联在 `main.qml` 中的浮动通知：

```qml
Rectangle {
    id: toast
    anchors.horizontalCenter: parent.horizontalCenter
    y: -50  // 初始隐藏在屏幕外
    Behavior on y {
        NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
    }

    function show(message) {
        toastText.text = message
        toast.color = Theme.successColor
        y = Theme.spacingXL       // 滑入
        timer.restart()           // 2s 后自动隐藏
    }

    function showError(message) {
        toastText.text = message
        toast.color = Theme.errorColor
        y = Theme.spacingXL
        errorTimer.restart()      // 3s 后自动隐藏
    }
}
```

### 触发源

```qml
Connections {
    target: settings
    function onConfigSaved() { toast.show("配置已保存") }
    function onConfigLoaded() { toast.show("配置已加载") }
    function onErrorOccurred(msg) { toast.showError(msg) }
}
```

## 7. 快捷键

```qml
Shortcut { sequences: [StandardKey.Save];  onActivated: settings.save() }
Shortcut { sequences: [StandardKey.Close]; onActivated: appWindow.close() }
Shortcut { sequences: [StandardKey.Quit];  onActivated: Qt.quit() }
Shortcut { sequence: "Meta+,";  onActivated: sidebar.currentIndex = 3 }  // 打开设置
Shortcut { sequences: ["Meta+Shift+S", "Ctrl+Shift+S"]; onActivated: toggle sidebar }
```
