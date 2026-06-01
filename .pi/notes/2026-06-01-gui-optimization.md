# PySide6 GUI 字体与页面结构优化方案

> 基于 `ui-ux-pro-max` skill 生成（product: Analytics Dashboard → Data-Dense + Minimalism）
> 生成时间：2026-06-01
> 范围：字体系统 + 页面结构（不含动画）

---

## 📊 诊断：当前问题

| 维度 | 现状 | 问题 |
|------|------|------|
| **字体族** | 仅定义 `fontMonospace`，正文用 Qt 默认 | 无系统 sans-serif 字体定义，无中英文体 fallback 链 |
| **字重** | 只有 `bold` / 默认两种 | 缺少 semibold(500)、medium(400)、light(300) 层级 |
| **字号** | Body 和 Heading 同为 13px，不可区分 | 字号重叠，层级不清晰 |
| **行高** | 未定义 | Qt 默认行高 ~1.2，正文偏挤（推荐 1.5-1.75） |
| **字间距** | 未定义 | 大写/英文场景无呼吸感 |
| **页面结构** | 5 个页面都是 `ScrollView > Column > SectionCard` 平铺 | 缺少页面类型差异化，视觉层级单调 |

---

## 一、🔤 字体方案优化

### 1.1 字体族选择

| 用途 | macOS 系统字体 | 跨平台 fallback | 理由 |
|------|---------------|-----------------|------|
| **正文/UI** | `SF Pro Text`, `SF Pro Display` | `PingFang SC`, `Inter`, `-apple-system`, `system-ui`, sans-serif | Apple HIG 原生感，PingFang SC 中文匹配 |
| **等宽/日志** | `SF Mono` | `Menlo`, `Monaco`, `Courier New`, monospace | 已有定义，补充完整 fallback |
| **数字/统计** | `SF Pro Display` | `Inter`, `-apple-system`, sans-serif | 大字号统计数字需要紧凑显示 |

### 1.2 THEME 新增字体属性（`main.py`）

```python
# ===== 字体族 =====
"fontFamilySans": "SF Pro Text, PingFang SC, Inter, -apple-system, system-ui, sans-serif",
"fontFamilyDisplay": "SF Pro Display, PingFang SC, Inter, -apple-system, system-ui, sans-serif",
"fontFamilyMono": "SF Mono, Menlo, Monaco, PingFang SC, Courier New, monospace",

# ===== 字重 =====
"weightLight":    300,
"weightRegular":  400,
"weightMedium":   500,
"weightSemibold": 600,
"weightBold":     700,

# ===== 行高（倍数） =====
"lineHeightTight":   1.2,   # 标题
"lineHeightNormal":  1.5,   # 正文
"lineHeightRelaxed": 1.75,  # 说明文字

# ===== 字间距 =====
"letterSpacingTight":  -0.2,  # 大标题
"letterSpacingNormal":  0,    # 正文
"letterSpacingWide":    0.5,  # 小写标签
```

### 1.3 字号层级重构

| 旧值 | 新值 | 用途 | 行高 | 字重 |
|------|------|------|------|------|
| `fontLargeTitle: 34` | **不变** | About 页面 Logo 标题 | 1.2 | 700 |
| `fontPageTitle: 28` | **不变** | 页面主标题 | 1.2 | 600 |
| ~~`fontTitle: 16`~~ | → **`18`** | SectionCard 区域标题 | 1.2 | 600 |
| ~~`fontHeading: 13`~~ | → **`15`** | 配置项标签/分组标题 | 1.2 | 500 |
| ~~`fontBody: 13`~~ | → **不变** | 正文、按钮文字、输入框 | 1.5 | 400 |
| *(新增)* | → **`fontBodySm: 12`** | 侧边栏项、状态标签 | 1.5 | 400 |
| ~~`fontCaption: 11`~~ | → **不变** | 辅助说明文字 | 1.5 | 400 |
| ~~`fontMini: 10`~~ | → **不变** | 日志文字、微型标签 | 1.75 | 400 |
| ~~`fontStat: 28`~~ | → **`32`** | 统计数字（成功/失败计数） | 1.2 | 700 |
| ~~`fontSidebarHeader: 12`~~ | → **`11`** | 侧边栏分组头 | 1.5 | 600 + 0.5 字间距 |

### 1.4 QML 字体使用规范

所有 Text 元素应统一使用：

```qml
// ✅ 标准模式
Text {
    text: "正文内容"
    font.family: Theme.fontFamilySans
    font.pixelSize: Theme.fontBody
    font.weight: Theme.weightRegular
    lineHeight: Theme.lineHeightNormal
}

// ✅ 标题模式
Text {
    text: "页面标题"
    font.family: Theme.fontFamilyDisplay
    font.pixelSize: Theme.fontPageTitle
    font.weight: Theme.weightSemibold
    lineHeight: Theme.lineHeightTight
    letterSpacing: Theme.letterSpacingTight
}

// ✅ 等宽模式（日志/代码）
Text {
    text: "log output"
    font.family: Theme.fontFamilyMono
    font.pixelSize: Theme.fontMini
    lineHeight: Theme.lineHeightRelaxed
}
```

---

## 二、📐 页面结构优化

### 2.1 页面类型区分

| 页面 | 类型 | 布局策略 | 内容宽度 |
|------|------|----------|----------|
| **HomePage** | 工作台（Workspace） | 当前 `ScrollView > Column > SectionCard` ✅ | `maxContentWidth: 680` |
| **SettingsPage** | 表单页（Form） | 分组卡片 + 粘性左侧标签 | `maxContentWidth: 760` 加宽 |
| **ToolsPage** | 卡片网格（Grid） | `GridLayout` 双列卡片 | `maxContentWidth: 840` |
| **LogPage** | 数据面板（Data Panel） | 顶栏过滤器 + 全屏等宽区域 | 全宽 |
| **AboutPage** | 信息页（Info） | 居中单卡片，限制宽度 | `aboutCardWidth: 400` |

### 2.2 SettingsPage —— 两栏布局

当前 376 行配置项平铺，扫视困难。改为左侧标签栏 + 右侧内容：

```
┌─── SettingsPage ──────────────────────────┐
│ ScrollView                                │
│ ┌───────────────────────────────────────┐ │
│ │ [通用]  ┃ 代理设置  ████████████████  │ │
│ │ [名称规则] ┃ 输入框...                │ │
│ │ [更新]  ┃ 开关...                    │ │
│ │ [日志]  ┃ 开关...                    │ │
│ │ [媒体]  ┃ ...                        │ │
│ │ [水印]  ┃ ...                        │ │
│ └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
  ← 粘性标签 →  ← 内容区域（自适应宽度）→
```

QML 结构：
```qml
ScrollView {
    Row {
        spacing: Theme.spacingXL
        // 左侧粘性标签栏
        Column {
            width: Theme.labelWidthWide
            spacing: Theme.spacingSM
            // 点击标签滚动到对应区域
        }
        // 右侧配置内容
        Column {
            spacing: Theme.spacingXXL
            SectionCard { sectionTitle: "通用" }
            SectionCard { sectionTitle: "代理" }
            // ...
        }
    }
}
```

### 2.3 ToolsPage —— 双列卡片网格

当前单列堆叠，空间浪费。改为双列 `GridLayout`：

```qml
ScrollView {
    Column {
        width: Math.min(parent.width - Theme.contentWidthPadding, Theme.maxContentWidth)
        spacing: Theme.spacingLG
        GridLayout {
            columns: 2
            columnSpacing: Theme.spacingLG
            rowSpacing: Theme.spacingLG
            ToolCard { Layout.fillWidth: true }
            ToolCard { Layout.fillWidth: true }
        }
    }
}
```

### 2.4 LogPage —— 全屏数据面板

移除 `maxContentWidth` 限制，日志区域全宽展示：

```qml
Column {
    anchors.horizontalCenter: parent.horizontalCenter
    width: parent.width - Theme.spacingXL * 2
    // 顶栏过滤器
    // LogViewer 全宽填充
}
```

### 2.5 SectionCard 增强 —— 可选描述区

```qml
SectionCard {
    sectionTitle: "处理模式"
    sectionDescription: "选择刮削或整理模式"  // 新增
}
```

SectionCard 内部实现：
```qml
Text {
    text: root.sectionDescription
    font.family: Theme.fontFamilySans
    font.pixelSize: Theme.fontCaption
    font.weight: Theme.weightRegular
    color: Theme.secondaryText
    lineHeight: Theme.lineHeightRelaxed
    visible: text !== ""
}
```

---

## 三、📋 修改清单

| 优先级 | 文件 | 改动 |
|--------|------|------|
| **P0** | `main.py` | 新增字体族、字重、行高、字间距常量；调整 `fontTitle`/`fontHeading`/`fontStat` 字号 |
| **P0** | `SectionCard.qml` | 新增 `sectionDescription` 属性；标题字号改用 `fontTitle` |
| **P1** | 所有 `*.qml` Text 元素 | 统一添加 `font.family: Theme.fontFamilySans` 和 `font.weight` |
| **P1** | `SettingsPage.qml` | 两栏布局重构（左侧标签栏 + 右侧内容） |
| **P2** | `ToolsPage.qml` | 单列 → 双列 `GridLayout` |
| **P2** | `LogPage.qml` | 移除 `maxContentWidth` 限制 |
| **P2** | `MacOSSidebar.qml` | 字体改用 `fontBodySm` + 分组头加宽字间距 |

---

## 四、⚠️ 注意事项（基于 skill UX 规则）

1. **中文可读性**：PingFang SC 在 11px 以下过小，`fontMini(10px)` 仅限等宽日志区使用
2. **对比度**：`secondaryText (#98989D)` 在 `#1E1E1E` 背景上对比度约 4.6:1，勉强达标（≥4.5:1）。caption 文字**不应**使用 `tertiaryText (#747476)`
3. **表单标签关联**：`ConfigInput` 等组件的 `labelText` 已有显式标签，符合 a11y 要求 ✅
4. **LineHeight 语法**：QML 中 `lineHeight` 属性接受绝对值（像素），如需倍数关系使用 `lineHeightMode: Text.ProportionalHeight`
