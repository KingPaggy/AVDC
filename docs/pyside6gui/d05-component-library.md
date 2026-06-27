# 组件库

> QML 组件属性速查、布局规范、SectionCard/Page 模式、新增组件步骤。

## 布局核心概念

### Layout 类型与子元素属性

| 父类型 | 子元素属性 | 说明 |
|--------|-----------|------|
| `ColumnLayout` / `RowLayout` / `GridLayout` | `Layout.*`（`Layout.fillWidth`、`Layout.preferredHeight`） | 自动布局 |
| `Column` / `Row` | `implicitHeight` / `implicitWidth` 或显式 `width`/`height` | **不能**使用 `Layout.*` |
| `Item` / `Rectangle` | 显式尺寸或子元素 `implicitHeight` | 基础类型 |

### implicitHeight 关键规则

1. **非 Layout 父元素**（如 `Column`）依赖子元素的 `implicitHeight` 确定自身高度
2. 子元素无 `implicitHeight` 且无显式 `height` → 父高度 = 0 → 内容不可见
3. 零高度父元素上 `anchors.fill: parent` → 循环依赖 → 布局失败

### SectionCard 模式

所有 SectionCard 使用 `ColumnLayout` 包裹子内容，通过 `implicitHeight` 自撑高度：

```qml
Rectangle {
    id: root
    radius: Theme.radiusLG
    color: Theme.cardBg
    implicitHeight: contentColumn.implicitHeight + Theme.spacingMD * 2

    default property alias contentData: contentColumn.children

    ColumnLayout {
        id: contentColumn
        width: parent.width - Theme.spacingMD * 2
        x: Theme.spacingMD
        y: Theme.spacingMD
        spacing: Theme.spacingSM
        // 标题 + 描述 + 分割线 + 子内容自动排列
    }
}
```

### Page Layout 模式

所有页面使用 `ScrollView > Column > SectionCard`：

```qml
ScrollView {
    anchors.fill: parent
    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - Theme.spacingXL * 2, Theme.maxContentWidth)
        spacing: Theme.spacingLG

        Item { implicitHeight: Theme.spacingXL }  // 顶部留白
        SectionCard { ... }
        SectionCard { ... }
        Item { implicitHeight: Theme.spacingXL }  // 底部留白
    }
}
```

---

## 组件速查表

### SectionCard — 分组容器

**文件**：`components/SectionCard.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `sectionTitle` | string | 标题文字 |
| `sectionDescription` | string | 描述文字（可选） |
| `contentData` | alias (default) | 子内容（直接写在 SectionCard 内） |

```qml
SectionCard {
    sectionTitle: "代理设置"
    sectionDescription: "配置网络代理"
    ConfigInput { labelText: "代理地址"; textValue: settings.proxy }
}
```

### ConfigInput — 文本输入

**文件**：`components/ConfigInput.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `labelText` | string | 左侧标签 |
| `textValue` | string | 输入值（双向绑定） |

内部使用 `_suppressUpdate` 标志防止双向绑定循环。

### ConfigFilePicker — 目录选择

**文件**：`components/ConfigFilePicker.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `labelText` | string | 左侧标签 |
| `textValue` | string | 路径值（双向绑定） |

使用 `Qt.labs.platform.FolderDialog` 弹出系统目录选择器。

### ConfigRadioGroup — 单选按钮组

**文件**：`components/ConfigRadioGroup.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `labelText` | string | 左侧标签 |
| `options` | var (array) | `[{value: int, text: string}, ...]` |
| `selectedValue` | var | 当前选中值（双向绑定） |

```qml
ConfigRadioGroup {
    labelText: "模式"
    options: [{value: 1, text: "刮削模式"}, {value: 2, text: "整理模式"}]
    selectedValue: settings.mainMode
}
```

### ConfigSwitch — 开关（bool）

**文件**：`components/ConfigSwitch.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `labelText` | string | 左侧标签 |
| `checked` | bool | 开关状态（双向绑定） |

### ConfigSwitchInt — 开关（int 0/1）

**文件**：`components/ConfigSwitchInt.qml`

与 ConfigSwitch 相同，但 `checked` 为 int（0/1），适配 `config.ini` 中的整型开关。

### ConfigSlider — 滑块

**文件**：`components/ConfigSlider.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `labelText` | string | 左侧标签 |
| `sliderValue` | real | 当前值 |
| `fromValue` | real | 最小值 |
| `toValue` | real | 最大值 |

### ConfigCheckbox — 复选框

**文件**：`components/ConfigCheckbox.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `labelText` | string | 标签 |
| `checked` | bool | 选中状态 |

### ProgressBar — 进度条

**文件**：`components/ProgressBar.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `progressValue` | real | 0.0 - 1.0 |
| `statusText` | string | 状态文字 |
| `showPercentage` | bool | 是否显示百分比 |

### LogViewer — 虚拟化日志列表

**文件**：`components/LogViewer.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `logModel` | var | 绑定 `logModel.filteredModel` |

内部使用 `ListView` + `QAbstractListModel`，只渲染可见行。级别徽章颜色通过 `readonly property var _levelColors` 查找表避免 delegate 内条件判断。

### ToolCard — 工具卡片

**文件**：`components/ToolCard.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `title` | string | 标题 |
| `description` | string | 描述 |
| `actionLabel` | string | 操作按钮文字（默认 "打开"） |
| `clicked` | signal | 点击信号 |

### StatusBadge — 状态徽章

**文件**：`components/StatusBadge.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `status` | string | `success` / `error` / `warning` / `info` |
| `text` | string | 徽章文字 |

### TitleBar — 自定义标题栏

**文件**：`components/TitleBar.qml`

| 组成 | 说明 |
|------|------|
| 拖拽区域 | MouseArea 覆盖左侧，手动计算窗口位移 |
| 标题文字 | 居中 "AVDC" |
| 侧边栏切换 | 左侧 TitleBarButton（展开/折叠图标） |
| 窗口控制 | 右侧 Row：最小化 / 最大化 / 关闭 |

### TitleBarButton — 窗口控制按钮

**文件**：`components/TitleBarButton.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `icon` | string | `minus` / `maximize` / `restore` / `close` / `expand` / `collapse` |
| `buttonColor` | color | 按钮颜色 |
| `clicked` | signal | 点击信号 |

### ResizeHandle — 边缘拖拽

**文件**：`components/ResizeHandle.qml`

| 属性 | 类型 | 说明 |
|------|------|------|
| `edge` | int | `Qt.TopEdge` / `BottomEdge` / `LeftEdge` / `RightEdge` |

按下时调用 `windowController.startResize(edge)`。

---

## 新增组件步骤

1. 在 `qml/components/` 创建 `XxxComponent.qml`
2. 声明对外属性（`property`）和信号（`signal`）
3. 设置 `implicitHeight`（如果被非 Layout 父元素包裹）
4. 使用 `Theme.*` 常量，不硬编码颜色/尺寸
5. 如需双向绑定，使用 `_suppressUpdate` 防循环模式
6. 添加 `Accessible.role` 和 `Accessible.name`
7. 在父页面中 `import "components"` 并使用
8. 运行 `.venv/bin/pyside6-qmllint` 检查语法

## 双向绑定防循环模式

```qml
// ConfigInput 中的做法
property bool _suppressUpdate: false

onTextValueChanged: {
    if (!_suppressUpdate && input.text !== textValue) {
        _suppressUpdate = true
        input.text = textValue
        _suppressUpdate = false
    }
}

TextField {
    onTextChanged: {
        if (!root._suppressUpdate && root.textValue !== text) {
            root.textValue = text
        }
    }
}
```

---

## 组件开发详解

### 开发 Checklist

| # | 检查项 | 原因 |
|---|--------|------|
| 1 | 使用 `Theme.*` 常量 | 不硬编码颜色/尺寸，保持视觉一致 |
| 2 | 设置 `implicitHeight` | 在非 Layout 父元素中自撑高度 |
| 3 | 双向绑定用 `_suppressUpdate` | 防止循环更新 |
| 4 | 添加 `Accessible.role` | 屏幕阅读器支持 |
| 5 | 使用 `Behavior on` | 交互动画平滑过渡 |
| 6 | 光标形状正确 | 可点击元素用 `PointingHandCursor` |
| 7 | 运行 `qmllint` | 检查语法错误 |

### 完整示例：开发 ConfigColorPicker

从 0 开发一个新的配置组件：

**步骤 1：创建组件文件**

```qml
// qml/components/ConfigColorPicker.qml
import QtQuick 2.15
import QtQuick.Layouts 1.15

RowLayout {
    id: root
    spacing: Theme.spacingSM

    // 对外属性
    property string labelText: ""
    property color colorValue: "#000000"

    // 内部状态
    property bool _suppressUpdate: false

    // 无障碍
    Accessible.role: Accessible.Group
    Accessible.name: labelText

    // 标签
    Text {
        text: labelText
        color: Theme.textColor
        font.pixelSize: Theme.fontBody
        Layout.preferredWidth: Theme.labelWidthWide
    }

    // 颜色预览 + 点击区域
    Rectangle {
        width: 40
        height: 24
        radius: Theme.radiusSM
        color: root.colorValue
        border.color: Theme.separatorColor
        border.width: 1

        Behavior on color {
            ColorAnimation { duration: Theme.animationFast }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: colorDialog.open()
        }
    }

    // 颜色值显示
    Text {
        text: root.colorValue.toString().toUpperCase()
        color: Theme.secondaryText
        font.pixelSize: Theme.fontBodySm
        font.family: Theme.fontMonospace
    }

    // 系统颜色选择器（Qt 6）
    Dialog {
        id: colorDialog
        title: "选择颜色"
        // ... 颜色选择逻辑
    }

    // 外部更新时同步内部状态
    onColorValueChanged: {
        if (!_suppressUpdate) {
            // 同步逻辑
        }
    }
}
```

**步骤 2：在页面中使用**

```qml
// SettingsPage.qml
SectionCard {
    sectionTitle: "主题设置"
    ConfigColorPicker {
        labelText: "强调色"
        colorValue: settings.accentColor
        onColorValueChanged: settings.accentColor = colorValue
    }
}
```

**步骤 3：添加 SCHEMA 字段（如需持久化）**

```python
# settings_model.py
SCHEMA = {
    # ...
    "accent_color": (str, "#0A84FF", "accentColor"),
}
```

**步骤 4：测试**

```python
# test/test_config_color_picker.py
def test_color_picker_default():
    """验证默认颜色值"""
    assert settings.accentColor == "#0A84FF"

def test_color_picker_change():
    """验证颜色变更信号"""
    spy = QSignalSpy(settings.accentColorChanged)
    settings.accentColor = "#FF0000"
    assert spy.count() == 1
```

### 性能优化

**1. Loader 延迟加载**

```qml
// 不推荐：所有页面立即实例化
Item {
    HomePage { visible: currentPage === 0 }
    SettingsPage { visible: currentPage === 1 }
}

// 推荐：使用 Loader 按需加载
Loader {
    id: pageLoader
    sourceComponent: currentPage === 0 ? homeComponent : settingsComponent

    Component { id: homeComponent; HomePage {} }
    Component { id: settingsComponent; SettingsPage {} }
}
```

**2. ListView 虚拟化**

```qml
// 不推荐：Repeater 实例化所有项
Repeater {
    model: 1000
    delegate: Rectangle { /* ... */ }
}

// 推荐：ListView 只渲染可见项
ListView {
    model: 1000
    delegate: Rectangle { /* ... */ }
    cacheBuffer: 100  // 缓存额外 100px
}
```

**3. 避免 delegate 内条件判断**

```qml
// 不推荐：每个 delegate 都计算颜色
delegate: Rectangle {
    color: {
        if (model.level === "ERROR") return Theme.errorColor
        if (model.level === "WARN") return Theme.warningColor
        return Theme.infoColor
    }
}

// 推荐：使用查找表
delegate: Rectangle {
    readonly property var _levelColors: ({
        "ERROR": Theme.errorColor,
        "WARN": Theme.warningColor,
        "INFO": Theme.infoColor
    })
    color: _levelColors[model.level] || Theme.infoColor
}
```

### 组件测试模板

```python
# test/test_my_component.py
import pytest
from PySide6.QtQML import QQmlApplicationEngine

class TestMyComponent:
    @pytest.fixture
    def engine(self, qt_app):
        engine = QQmlApplicationEngine()
        engine.rootContext().setContextProperty("Theme", THEME)
        engine.load("qml/components/MyComponent.qml")
        return engine

    def test_loads_without_error(self, engine):
        """验证组件可加载"""
        assert len(engine.rootObjects()) > 0

    def test_default_property_values(self, engine):
        """验证默认属性值"""
        root = engine.rootObjects()[0]
        assert root.property("myProperty") == "default"

    def test_signal_emitted_on_change(self, engine):
        """验证信号发射"""
        root = engine.rootObjects()[0]
        spy = QSignalSpy(root.mySignal)
        root.setProperty("myProperty", "new_value")
        assert spy.count() == 1
```
