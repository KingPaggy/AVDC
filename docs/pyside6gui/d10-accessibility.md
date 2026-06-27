# 无障碍访问指南

> QML Accessible 属性、键盘导航、屏幕阅读器支持、Apple HIG 无障碍要求。

## 1. 无障碍基础

### 为什么需要无障碍

- 法规要求（WCAG 2.1、ADA、Section 508）
- 扩大用户群体（视障、运动障碍用户）
- 提升整体用户体验

### Qt 无障碍架构

```
QML Component
    ↓ Accessible.role/name/description
Qt Accessibility API
    ↓ 平台适配
OS Screen Reader（VoiceOver/NVDA/Orca）
```

## 2. Accessible 属性

### 核心属性

| 属性 | 类型 | 用途 |
|------|------|------|
| `Accessible.role` | enum | 组件角色（Button/TextField/Slider 等） |
| `Accessible.name` | string | 组件名称（屏幕阅读器朗读） |
| `Accessible.description` | string | 详细描述（可选） |
| `Accessible.state` | int | 状态标志（checked/disabled 等） |

### 角色枚举

```qml
Accessible.role: Accessible.Button     // 按钮
Accessible.role: Accessible.TextField  // 文本输入
Accessible.role: Accessible.Slider     // 滑块
Accessible.role: Accessible.CheckBox   // 复选框
Accessible.role: Accessible.RadioButton // 单选按钮
Accessible.role: Accessible.Tab        // 标签页
Accessible.role: Accessible.MenuItem   // 菜单项
```

## 3. 组件无障碍实现

### 按钮组件

```qml
Rectangle {
    id: root
    Accessible.role: Accessible.Button
    Accessible.name: "保存配置"
    Accessible.description: "将当前设置写入 config.ini"
    Accessible.onPressAction: root.clicked()  // 键盘激活
    
    signal clicked()
    
    MouseArea {
        anchors.fill: parent
        onClicked: root.clicked()
    }
}
```

### 输入框组件

```qml
TextField {
    id: input
    Accessible.role: Accessible.TextField
    Accessible.name: "代理地址"
    placeholderText: "例如：http://127.0.0.1:7890"
    
    // 状态：聚焦时自动设置
    Accessible.state: activeFocus ? 
        Accessible.StateFocused : 
        Accessible.StateDefault
}
```

### 滑块组件

```qml
Slider {
    id: slider
    Accessible.role: Accessible.Slider
    Accessible.name: "超时时间"
    Accessible.valueText: slider.value + " 秒"  // 朗读值
    
    // 键盘控制：← → 调整值（Slider 默认支持）
}
```

## 4. 键盘导航

### Tab 顺序

QML 默认按声明顺序 Tab，可通过 `focusPolicy` 控制：

```qml
TextField {
    focusPolicy: Qt.StrongFocus  // 可 Tab 聚焦
}

Text {
    focusPolicy: Qt.NoFocus      // 跳过（默认）
}
```

### 快捷键

```qml
// 全局快捷键（main.qml）
Shortcut {
    sequence: StandardKey.Save  // Ctrl+S / Cmd+S
    onActivated: settings.save()
}

// 按钮访问键
Button {
    text: "&保存"  // Alt+S 激活
}
```

## 5. 项目现状与待办

### 已实现

- TitleBarButton：`Accessible.role: Button` + `onPressAction`
- ToolCard：`Accessible.role: Button` + `name/description`
- MacOSSidebar 导航项：`Accessible.role: Button`

### 待实现

- Config* 组件的 `Accessible.name`（当前缺失）
- LogViewer 的 `Accessible.role: List`
- 页面切换的焦点管理
- 高对比度模式支持

## 6. 测试方法

### 手动测试

```bash
# macOS VoiceOver
Cmd+F5  # 开启
Ctrl+Option+A  # 朗读当前组件

# Windows NVDA
Insert+N  # 打开菜单
Ctrl+Alt+T  # 朗读当前组件
```

### 自动化测试

```python
# 验证 Accessible 属性已设置
def test_accessible_name():
    button = find_qquickitem_by_name(root, "saveButton")
    assert button.Accessible.name == "保存配置"
```
