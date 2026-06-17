# 动画与交互

> QML 动画机制、状态过渡、Timer 使用、快捷键系统。

## 动画常量

所有动画时长由 `Theme` 统一管理：

| 常量 | 值 | 场景 |
|------|-----|------|
| `Theme.animationFast` | 150ms | hover 颜色过渡、边框变化 |
| `Theme.animationNormal` | 300ms | Toast 滑入/滑出 |
| `Theme.animationSlow` | 500ms | 页面过渡（未启用） |

## Behavior — 属性变化自动动画

`Behavior on` 监听属性变化，自动播放动画。项目中大量使用：

### 颜色过渡（hover/选中态）

```qml
// ToolCard.qml — 悬停时背景色和边框色渐变
Rectangle {
    color: mouseArea.containsMouse ? Theme.hoverBg : Theme.cardBg
    border.color: mouseArea.containsMouse ? Theme.accentColor : Theme.separatorColor

    Behavior on color {
        ColorAnimation { duration: Theme.animationFast }
    }
    Behavior on border.color {
        ColorAnimation { duration: Theme.animationFast }
    }
}
```

```qml
// MacOSSidebar.qml — 导航项 hover 背景
Rectangle {
    color: mouseArea.containsMouse ? Theme.hoverBg : "transparent"
    Behavior on color {
        ColorAnimation { duration: Theme.animationFast }
    }
}
```

```qml
// TitleBarButton.qml — 按钮 hover
Rectangle {
    color: mouseArea.containsMouse ? Qt.lighter(buttonColor, 1.3) : "transparent"
    Behavior on color {
        ColorAnimation { duration: Theme.animationFast }
    }
}
```

### 位移动画（Toast）

```qml
// main.qml — Toast 滑入/滑出
Rectangle {
    id: toast
    y: -50  // 初始隐藏在屏幕外
    Behavior on y {
        NumberAnimation {
            duration: Theme.animationNormal  // 300ms
            easing.type: Easing.OutCubic     // 缓出曲线
        }
    }
}
```

### 文字颜色过渡

```qml
// ToolCard.qml — 操作按钮文字颜色
Text {
    color: mouseArea.containsMouse ? Theme.accentColor : Theme.tertiaryText
    Behavior on color { ColorAnimation { duration: Theme.animationFast } }
}
```

## NumberAnimation — 显式动画

用于需要精确控制的场景（如 ProgressBar，当前未启用动画）：

```qml
// 可用于 ProgressBar 的动画方案（当前未启用）
Rectangle {
    width: parent.width * progressValue
    Behavior on width {
        NumberAnimation { duration: 200; easing.type: Easing.OutQuad }
    }
}
```

## Timer — 定时触发

### Toast 自动隐藏

```qml
Timer {
    id: timer
    interval: Theme.toastDuration  // 2000ms
    onTriggered: toast.y = -50     // 滑出屏幕
}

Timer {
    id: errorTimer
    interval: Theme.toastErrorDuration  // 3000ms（错误消息更长）
    onTriggered: toast.y = -50
}
```

### 日志自动滚动

```qml
// LogViewer.qml — 防抖自动滚动
ListView {
    onCountChanged: {
        if (count > 0 && !atYEnd) {
            autoScrollTimer.start()
        }
    }

    Timer {
        id: autoScrollTimer
        interval: 50  // 50ms 防抖
        onTriggered: parent.positionViewAtEnd()
    }
}
```

**设计要点**：使用 Timer 防抖而非直接在 `onCountChanged` 中滚动，避免高频日志时频繁滚动导致卡顿。

## 状态过渡图

### 按钮/卡片交互状态

```
┌──────────┐   mouseEnter   ┌──────────┐   mousePress   ┌──────────┐
│  默认态   │ ────────────→ │  悬停态   │ ────────────→ │  按下态   │
│ transparent│               │  hoverBg  │               │ pressedBg │
└──────────┘ ←──────────── └──────────┘ ←──────────── └──────────┘
                 mouseExit                 mouseRelease

┌──────────┐   activeFocus  ┌──────────┐
│  默认态   │ ────────────→ │  聚焦态   │
│           │               │ focusBorder│
└──────────┘ ←──────────── └──────────┘
                 focusLost

┌──────────┐   enabled:false ┌──────────┐
│  任意态   │ ─────────────→ │  禁用态   │
│           │                │ opacity 0.5│
└──────────┘ ←───────────── └──────────┘
                 enabled:true
```

### 侧边栏导航项状态

```
默认态：  文字 textColor，无边框
选中态：  文字 accentColor + 左侧 indicator（accentColor 3px）
悬停态：  背景 hoverBg（Behavior 150ms）
选中+悬停：文字 accentColor + 背景 hoverBg + indicator
```

### 输入框状态

```
默认态：  背景 inputBg，边框 separatorColor
聚焦态：  背景 inputBg，边框 focusBorder (accentColor)
错误态：  边框 errorColor（手动设置）
禁用态：  opacity 0.5
```

## 快捷键

### 全局快捷键（main.qml）

| 快捷键 | 动作 |
|--------|------|
| `Ctrl+S` / `Cmd+S` | 保存配置 |
| `Ctrl+W` / `Cmd+W` | 关闭窗口 |
| `Ctrl+Q` / `Cmd+Q` | 退出应用 |
| `Cmd+,` | 切换到设置页 |
| `Ctrl+Shift+S` / `Cmd+Shift+S` | 切换侧边栏折叠 |

### 待实现的快捷键

```qml
Shortcut { sequences: [StandardKey.New];   onActivated: toast.show("新建窗口（待实现）") }
Shortcut { sequences: [StandardKey.Open];  onActivated: toast.show("打开文件（待实现）") }
Shortcut { sequences: [StandardKey.Undo];  onActivated: toast.show("撤销（待实现）") }
Shortcut { sequences: [StandardKey.Redo];  onActivated: toast.show("重做（待实现）") }
```

## 光标形状

| 场景 | 光标 |
|------|------|
| 可点击元素（按钮/卡片/导航项） | `Qt.PointingHandCursor` |
| 窗口边缘拖拽（上下） | `Qt.SizeVerCursor` |
| 窗口边缘拖拽（左右） | `Qt.SizeHorCursor` |
| 默认 | `Qt.ArrowCursor` |

## 可访问性

所有交互组件设置了 Accessible 属性：

```qml
Accessible.role: Accessible.Button
Accessible.name: "关闭"
Accessible.description: "关闭应用程序"
Accessible.onPressAction: { /* 等同于 onClicked */ }
```

支持的组件：TitleBarButton、ToolCard、MacOSSidebar 导航项。
