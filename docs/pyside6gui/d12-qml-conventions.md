# QML 代码规范

> 项目 QML 代码的命名、布局、import 顺序、注释风格等约定。

## 1. 文件命名

### 规则

- **PascalCase**：每个单词首字母大写
- **页面文件**：`XxxPage.qml`（HomePage、SettingsPage）
- **组件文件**：`XxxComponent.qml`（ConfigInput、SectionCard）
- **特殊组件**：保持描述性名称（MacOSSidebar、TitleBar）

### 示例

```
pyside6_gui/qml/
├── HomePage.qml          ✅ 页面
├── SettingsPage.qml      ✅ 页面
├── MacOSSidebar.qml      ✅ 特殊组件
└── components/
    ├── ConfigInput.qml   ✅ 配置组件
    ├── SectionCard.qml   ✅ 容器组件
    └── TitleBar.qml      ✅ 窗口组件
```

---

## 2. import 顺序

### 规则

按以下顺序排列 import 语句：

1. `QtQuick 2.15`
2. `QtQuick.Controls 2.15`
3. `QtQuick.Layouts 2.15`
4. `Qt.labs.platform 1.1`（如需要）
5. `"components"`（本地组件目录）

### 示例

```qml
import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1 as LabPlatform
import "components"
```

### 为什么

- 统一顺序便于快速定位依赖
- 本地组件放最后，避免和 Qt 模块混淆

---

## 3. 属性命名

### 规则

- **camelCase**：首字母小写，后续单词首字母大写
- **双向绑定属性**：用 `Value` 后缀（`textValue`、`sliderValue`）
- **信号命名**：camelCase 动词（`clicked`、`textValueChanged`）
- **内部属性**：用 `_` 前缀（`_suppressUpdate`、`_levelColors`）

### 示例

```qml
// ✅ 正确
property string labelText: ""
property string textValue: ""
signal clicked()
property bool _suppressUpdate: false

// ❌ 错误
property string LabelText: ""      // PascalCase
property string text_value: ""     // snake_case
signal Clicked()                   // 信号不应大写
```

---

## 4. 颜色与尺寸

### 规则

- **必须使用 `Theme.*` 常量**，禁止硬编码颜色/尺寸
- **颜色**：`Theme.textColor`、`Theme.accentColor`
- **间距**：`Theme.spacingSM`、`Theme.spacingMD`
- **圆角**：`Theme.radiusSM`、`Theme.radiusLG`
- **字号**：`Theme.fontBody`、`Theme.fontHeading`

### 示例

```qml
// ✅ 正确
Rectangle {
    color: Theme.cardBg
    radius: Theme.radiusLG
    Layout.preferredWidth: Theme.sidebarIdeal
}

// ❌ 错误
Rectangle {
    color: "#2D2D2D"              // 硬编码颜色
    radius: 8                     // 硬编码尺寸
    Layout.preferredWidth: 240    // 硬编码尺寸
}
```

### 为什么

- 统一视觉风格
- 方便主题切换（如未来支持 Light Mode）
- 修改一处，全局生效

---

## 5. 布局模式

### 规则

- **页面布局**：`ScrollView` + `Column` + `SectionCard`
- **组件布局**：`Column`/`Row` + `implicitHeight`
- **不用 `ColumnLayout`**：除非需要 `Layout.*` 属性

### 页面模板

```qml
Item {
    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: width

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
}
```

### 组件模板

```qml
RowLayout {
    id: root
    spacing: Theme.spacingSM

    property string labelText: ""
    property string textValue: ""

    implicitHeight: childrenRect.height  // 自撑高度

    Text {
        text: root.labelText
        color: Theme.textColor
        Layout.preferredWidth: Theme.labelWidthWide
    }

    TextField {
        id: input
        text: root.textValue
        Layout.fillWidth: true
    }
}
```

### 为什么不用 ColumnLayout？

- `ColumnLayout` 子元素必须用 `Layout.*` 属性
- 和 `SectionCard` 的 `default property alias contentData` 不兼容
- `Column` + `implicitHeight` 更灵活

---

## 6. 注释风格

### 规则

- **文件开头**：`// 文件名 — 用途说明`
- **关键逻辑**：`// 说明`（简短）
- **不写显而易见的注释**

### 示例

```qml
// ConfigInput.qml — Label + TextField for string config values

RowLayout {
    id: root

    // 双向绑定防循环标志
    property bool _suppressUpdate: false

    Text {
        text: root.labelText
        color: Theme.textColor
    }

    TextField {
        id: input
        text: root.textValue

        // 用户输入时更新绑定值
        onTextChanged: {
            if (!root._suppressUpdate && root.textValue !== text) {
                root.textValue = text
            }
        }
    }
}
```

### 为什么

- 文件头注释便于快速定位
- 关键逻辑注释解释"为什么"，不是"做什么"
- 显而易见的代码不需要注释（如 `color: Theme.textColor`）

---

## 7. 信号与事件

### 规则

- **信号命名**：camelCase 动词（`clicked`、`textValueChanged`）
- **信号参数**：camelCase（`textValue: string`）
- **事件处理**：`onXxx` 前缀（`onClicked`、`onTextChanged`）

### 示例

```qml
// 声明信号
signal clicked()
signal textValueChanged(textValue: string)

// 发射信号
onClicked: root.clicked()

// 接收信号
Button {
    onClicked: console.log("clicked")
}
```

---

## 8. 动画

### 规则

- **使用 `Behavior on`**：属性变化自动动画
- **时长**：`Theme.animationFast`（150ms）或 `Theme.animationNormal`（300ms）
- **缓动**：`Easing.OutCubic`（缓出）

### 示例

```qml
Rectangle {
    color: mouseArea.containsMouse ? Theme.hoverBg : Theme.cardBg

    Behavior on color {
        ColorAnimation {
            duration: Theme.animationFast
            easing.type: Easing.OutCubic
        }
    }
}
```

---

## 9. 可访问性

### 规则

- **所有交互组件**：设置 `Accessible.role` 和 `Accessible.name`
- **按钮**：`Accessible.role: Accessible.Button`
- **输入框**：`Accessible.role: Accessible.TextField`

### 示例

```qml
Button {
    text: "保存"
    Accessible.role: Accessible.Button
    Accessible.name: "保存配置"
    Accessible.description: "将当前设置写入 config.ini"
}
```

---

## 10. Checklist

新建或修改 QML 文件前，检查以下项目：

- [ ] 文件名 PascalCase
- [ ] import 顺序正确
- [ ] 属性命名 camelCase
- [ ] 颜色/尺寸用 Theme.*
- [ ] 布局用 Column/Row + implicitHeight
- [ ] 文件头有注释
- [ ] 交互组件有 Accessible 属性
- [ ] 运行 `qmllint` 检查语法
