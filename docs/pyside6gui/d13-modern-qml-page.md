# 编写现代化 QML 页面

> 现代样式、流畅动画、高性能响应 — 实用技巧与参考链接。

## 1. 现代样式

### 设计原则

- **语义化颜色**：用 `accentColor`、`errorColor` 而非 `blueColor`、`redColor`，便于主题切换
- **层级感**：通过背景色灰度差异（而非边框）区分区域，如 `#1E1E1E` → `#2D2D2D` → `#3A3A3C`
- **留白**：内容四周至少 20px 边距，元素间距 8-16px
- **圆角**：现代 UI 普遍使用圆角（6-12px），避免生硬直角
- **字体层级**：标题 15-18px、正文 13-14px、辅助文字 11-12px

### 参考链接

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/foundations/color) — 色彩、排版、间距的行业标杆
- [Material Design 3](https://m3.material.io/styles/color/overview) — Google 的设计系统，色彩令牌概念
- [Qt Style System](https://doc.qt.io/qt-6/qtquickcontrols2-styles.html) — Qt Quick Controls 内置样式
- [QML Styling](https://doc.qt.io/qt-6/qml-qtquick-controls2-qquickstyle.html) — 自定义控件外观

---

## 2. 流畅动画

### 核心概念

| 方式 | 适用场景 | 示例 |
|------|----------|------|
| `Behavior on` | 属性变化时自动播放动画 | hover 颜色过渡、位置移动 |
| `NumberAnimation` | 精确控制时长、缓动曲线 | 按钮按下缩放 |
| `PropertyAnimation` | 通用属性动画 | 透明度渐变 |
| `ParallelAnimation` | 多个动画同时播放 | 淡入 + 位移 |
| `SequentialAnimation` | 动画依次播放 | 弹跳效果 |

### 缓动曲线

| 曲线 | 用途 | 感受 |
|------|------|------|
| `Easing.OutCubic` | 元素出现 | 快速进入、缓慢停止 |
| `Easing.InCubic` | 元素消失 | 缓慢启动、快速离开 |
| `Easing.InOutCubic` | 位置移动 | 对称的加速减速 |
| `Easing.OutBounce` | 趣味反馈 | 弹跳效果 |

### 推荐时长

| 类型 | 时长 | 场景 |
|------|------|------|
| 微交互 | 100-150ms | hover 颜色、按钮按下 |
| 中等过渡 | 200-300ms | 页面切换、Toast 滑入 |
| 复杂动画 | 400-500ms | 列表项展开、模态框 |

### 示例

```qml
Rectangle {
    id: card
    color: Theme.cardBg
    radius: Theme.radiusLG

    // 悬停时背景色平滑过渡
    Behavior on color {
        ColorAnimation {
            duration: 150
            easing.type: Easing.OutCubic
        }
    }

    // 按下时轻微缩放
    scale: mouseArea.pressed ? 0.98 : 1.0
    Behavior on scale {
        NumberAnimation {
            duration: 100
            easing.type: Easing.OutCubic
        }
    }
}
```

### 参考链接

- [QML Animation and Transitions](https://doc.qt.io/qt-6/qtquick-animation-topic.html) — 动画系统总览
- [Behavior Type](https://doc.qt.io/qt-6/qml-qtquick-behavior.html) — 属性变化自动动画
- [PropertyAnimation](https://doc.qt.io/qt-6/qml-qtquick-propertyanimation.html) — 通用属性动画
- [Easing Curves](https://doc.qt.io/qt-6/qml-qtquick-propertyanimation.html#easing.type-prop) — 缓动曲线类型与可视化
- [Qt Quick Examples - Animation](https://doc.qt.io/qt-6/qtquick-animation-example.html) — 官方动画示例集
- [Easing Curve Cheat Sheet](https://easings.net/) — 缓动曲线在线预览

---

## 3. 高性能响应

### ListView 虚拟化

```qml
// ✅ 推荐：ListView 只渲染可见行
ListView {
    model: logModel
    delegate: LogDelegate {}
    cacheBuffer: 100  // 额外缓存 100px，滚动更平滑
}

// ❌ 避免：Repeater 实例化所有项
Repeater {
    model: 1000
    delegate: Rectangle {}  // 1000 个 Rectangle 同时存在
}
```

### Loader 延迟加载

```qml
// ✅ 按需加载页面
Loader {
    id: pageLoader
    sourceComponent: currentPage === 0 ? homeComponent : null

    Component { id: homeComponent; HomePage {} }
}

// ❌ 避免：所有页面同时存在
Item {
    HomePage { visible: currentPage === 0 }  // 始终在内存中
    SettingsPage { visible: currentPage === 1 }
}
```

### 异步图片加载

```qml
Image {
    source: "image://provider/large_photo"
    asynchronous: true  // 后台线程加载
    cache: true         // 缓存已加载的图片
}
```

### 避免 Binding 循环

```qml
// ❌ 绑定循环
TextField {
    text: root.value
    onTextChanged: root.value = text  // 无限循环
}

// ✅ 使用 _suppressUpdate 标志
property bool _suppressUpdate: false

TextField {
    text: root.value
    onTextChanged: {
        if (!root._suppressUpdate) {
            root._suppressUpdate = true
            root.value = text
            root._suppressUpdate = false
        }
    }
}

onValueChanged: {
    if (!_suppressUpdate) {
        _suppressUpdate = true
        textField.text = value
        _suppressUpdate = false
    }
}
```

### 性能分析工具

| 工具 | 用途 | 链接 |
|------|------|------|
| Qt Creator QML Profiler | 帧率、绑定耗时、内存 | [文档](https://doc.qt.io/qtcreator/creator-qml-performance-monitor.html) |
| QML Debugging | 断点、变量查看 | [文档](https://doc.qt.io/qt-6/qtquick-debugging.html) |
| Qt Quick Renderer Debug | 渲染节点可视化 | 设置 `QSG_INFO=1` 环境变量 |

### 参考链接

- [QML Performance](https://doc.qt.io/qt-6/qtquick-performance.html) — 官方性能优化指南
- [Efficient JavaScript](https://doc.qt.io/qt-6/qtquick-javascript-topic.html#efficient-javascript) — JS 代码优化
- [Qt Quick Best Practices](https://doc.qt.io/qt-6/qtquick-best-practices.html) — 架构与性能最佳实践
- [QML Global Object](https://doc.qt.io/qt-6/qml-qtqml-qt.html) — Qt 全局对象（定时器、国际化等）

---

## 4. 交互反馈

### 状态机

```qml
Item {
    id: button
    state: "normal"

    states: [
        State {
            name: "hovered"
            PropertyChanges { target: bg; color: Theme.hoverBg }
        },
        State {
            name: "pressed"
            PropertyChanges { target: bg; color: Theme.pressedBg; scale: 0.98 }
        }
    ]

    transitions: [
        Transition {
            from: "*"; to: "*"
            ColorAnimation { duration: 150 }
            NumberAnimation { property: "scale"; duration: 100 }
        }
    ]
}
```

### 参考链接

- [Qt Quick States](https://doc.qt.io/qt-6/qml-qtquick-state.html) — 状态定义
- [Qt Quick Transitions](https://doc.qt.io/qt-6/qml-qtquick-transition.html) — 状态切换动画
- [Qt Quick Controls Interaction](https://doc.qt.io/qt-6/qtquickcontrols2-interaction.html) — 控件交互模式

---

## 5. 响应式布局

### 窗口尺寸适配

```qml
Item {
    readonly property bool isCompact: width < 600
    readonly property bool isStandard: width >= 900

    Column {
        spacing: isCompact ? 8 : 16

        // 紧凑模式隐藏次要内容
        Text {
            text: "详细说明"
            visible: !isCompact
        }
    }
}
```

### 动态内容宽度

```qml
Column {
    anchors.horizontalCenter: parent.horizontalCenter
    width: Math.min(parent.width - 40, 680)  // 最大 680px，两侧留 20px
}
```

### 参考链接

- [Qt Quick Layouts](https://doc.qt.io/qt-6/qtquicklayouts-index.html) — Layout 系统文档
- [Responsive UI](https://doc.qt.io/qt-6/qtquickcontrols2-layout.html) — 控件布局指南
- [Anchor Layouts](https://doc.qt.io/qt-6/qtquick-positioning-anchors.html) — 锚点布局

---

## 6. 综合示例：现代卡片组件

```qml
// ModernCard.qml — 完整示例
import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root

    // 对外接口
    property string title: ""
    property string description: ""
    signal clicked()

    // 样式
    width: 320
    height: 120
    radius: 12
    color: mouseArea.containsMouse ? "#2D2D2D" : "#1E1E1E"
    border.color: mouseArea.containsMouse ? "#0A84FF" : "#424245"
    border.width: 1

    // 悬停动画
    Behavior on color {
        ColorAnimation { duration: 150; easing.type: Easing.OutCubic }
    }
    Behavior on border.color {
        ColorAnimation { duration: 150; easing.type: Easing.OutCubic }
    }

    // 按下缩放
    scale: mouseArea.pressed ? 0.98 : 1.0
    Behavior on scale {
        NumberAnimation { duration: 100; easing.type: Easing.OutCubic }
    }

    // 内容
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 8

        Text {
            text: root.title
            font.pixelSize: 15
            font.weight: Font.Medium
            color: "#F5F5F7"
            Layout.fillWidth: true
        }

        Text {
            text: root.description
            font.pixelSize: 12
            color: "#98989D"
            Layout.fillWidth: true
            wrapMode: Text.WordWrap
        }

        Item { Layout.fillHeight: true }  // 弹性空间
    }

    // 交互
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    // 无障碍
    Accessible.role: Accessible.Button
    Accessible.name: root.title
    Accessible.description: root.description
}
```

---

## 7. 学习资源汇总

### 官方文档

| 资源 | 链接 |
|------|------|
| QML Book | [qmlbook.github.io](https://qmlbook.github.io/) — 免费在线教程 |
| Qt Quick Tutorials | [doc.qt.io/qt-6/qtquick-index.html](https://doc.qt.io/qt-6/qtquick-index.html) |
| QML Types | [doc.qt.io/qt-6/qmltypes.html](https://doc.qt.io/qt-6/qmltypes.html) — 类型索引 |
| Qt Quick Controls Gallery | [doc.qt.io/qt-6/qtquickcontrols2-gallery.html](https://doc.qt.io/qt-6/qtquickcontrols2-gallery.html) |

### 设计参考

| 资源 | 链接 |
|------|------|
| Apple HIG | [developer.apple.com/design](https://developer.apple.com/design/human-interface-guidelines) |
| Material Design | [m3.material.io](https://m3.material.io/) |
| Fluent Design | [learn.microsoft.com/fluent-design](https://learn.microsoft.com/en-us/fluent-design/) |
| Dribbble QML | [dribbble.com/tag/qml](https://dribbble.com/tags/qml) — 设计灵感 |

### 性能优化

| 资源 | 链接 |
|------|------|
| Qt Quick Performance | [doc.qt.io/qt-6/qtquick-performance.html](https://doc.qt.io/qt-6/qtquick-performance.html) |
| QML Profiler | [doc.qt.io/qtcreator/creator-qml-performance-monitor.html](https://doc.qt.io/qtcreator/creator-qml-performance-monitor.html) |
| Qt Best Practices | [doc.qt.io/qt-6/qtquick-best-practices.html](https://doc.qt.io/qt-6/qtquick-best-practices.html) |

### 社区

| 资源 | 链接 |
|------|------|
| Qt Forum | [forum.qt.io](https://forum.qt.io/) — 官方论坛 |
| Stack Overflow [qml] | [stackoverflow.com/questions/tagged/qml](https://stackoverflow.com/questions/tagged/qml) |
| Qt Quick Examples | [doc.qt.io/qt-6/qtquick-codesamples.html](https://doc.qt.io/qt-6/qtquick-codesamples.html) |
