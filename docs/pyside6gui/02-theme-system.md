# Theme 系统

> Apple HIG 风格主题常量定义，通过 Context Property 暴露给 QML，实现全局统一视觉。

## 设计理念

- **Apple HIG 平台无关**：语义化颜色命名，不绑定特定平台
- **Dark Mode 默认**：所有颜色基于深色背景
- **8pt 网格**：间距均为 4 的倍数
- **集中管理**：所有视觉参数在 `main.py` 的 `THEME` dict 中定义，QML 只读引用

## 注入方式

```python
# main.py
THEME = { ... }  # 所有常量
engine.rootContext().setContextProperty("Theme", THEME)
```

```qml
// QML 任意位置
color: Theme.accentColor
font.pixelSize: Theme.fontBody
Layout.preferredWidth: Theme.sidebarIdeal
```

## 颜色体系

### 文字颜色

| 名称 | 色值 | 用途 |
|------|------|------|
| `textColor` | `#F5F5F7` | 主文字、标题 |
| `secondaryText` | `#98989D` | 标签、描述 |
| `tertiaryText` | `#747476` | 占位符、弱文字 |

### 语义颜色

| 名称 | 色值 | 用途 |
|------|------|------|
| `accentColor` | `#0A84FF` | 聚焦边框、链接、激活态、侧边栏选中 |
| `errorColor` | `#FF453A` | 错误提示、关闭按钮 |
| `successColor` | `#30D158` | 成功提示、最小化按钮 |
| `warningColor` | `#FF9F0A` | 警告状态、最大化按钮 |
| `infoColor` | `#64D2FF` | 信息提示 |

### 装饰颜色

| 名称 | 色值 | 用途 |
|------|------|------|
| `purpleColor` | `#BF5AF2` | 可选强调 |
| `pinkColor` | `#FF375F` | 可选强调 |
| `mintColor` | `#66E0D8` | 可选强调 |
| `indigoColor` | `#5E5CE6` | 可选强调 |
| `yellowColor` | `#FFD60A` | 可选强调 |
| `brownColor` | `#AC8E68` | 可选强调 |

### 背景颜色

| 名称 | 色值 | 用途 |
|------|------|------|
| `backgroundColor` | `#1E1E1E` | ApplicationWindow 底色 |
| `sidebarBg` | `#2D2D2D` | 侧边栏背景 |
| `cardBg` | `#2D2D2D` | 卡片、SectionCard 背景 |
| `inputBg` | `#3A3A3C` | 输入框背景 |
| `separatorColor` | `#424245` | 分割线、非聚焦边框 |

### 交互颜色

| 名称 | 色值 | 用途 |
|------|------|------|
| `hoverBg` | `#3A3A3C` | 悬停背景 |
| `pressedBg` | `#48484A` | 按下背景 |
| `focusBorder` | `#0A84FF` | 聚焦边框（同 accentColor） |

## 间距（8pt 网格）

| 名称 | 值 | 用途 |
|------|-----|------|
| `spacingXS` | 4 | 极小间距 |
| `spacingSM` | 8 | 小组件间距 |
| `spacingMD` | 12 | SectionCard 内边距 |
| `spacingLG` | 16 | 页面区块间距 |
| `spacingXL` | 20 | 页面边距 |
| `spacingXXL` | 24 | 大区块间距 |
| `spacingXXXL` | 32 | 页面顶/底留白 |

## 圆角

| 名称 | 值 | 用途 |
|------|-----|------|
| `radiusXS` | 2 | 指示器 |
| `radiusSM` | 4 | 小按钮、徽章 |
| `radiusMD` | 6 | 输入框、进度条 |
| `radiusLG` | 8 | 卡片、面板 |
| `radiusXL` | 12 | 窗口圆角、Toast |

## 字号层级

| 名称 | 值 | 用途 |
|------|-----|------|
| `fontMini` | 10 | 日志时间戳、极小标注 |
| `fontCaption` | 11 | 数值标签、状态标签、侧边栏 header |
| `fontBodySm` | 12 | 次要正文、侧边栏导航文字 |
| `fontBody` | 13 | 正文、标签、按钮文字 |
| `fontHeading` | 15 | 区块标题 |
| `fontTitle` | 18 | SectionCard 标题 |
| `fontPageTitle` | 28 | 页面主标题 |
| `fontLargeTitle` | 34 | 超大标题 |
| `fontStat` | 32 | 统计数字 |

## 字重

| 名称 | 值 |
|------|-----|
| `weightLight` | 300 |
| `weightRegular` | 400 |
| `weightMedium` | 500 |
| `weightSemibold` | 600 |
| `weightBold` | 700 |

## 字体族

| 名称 | 值 | 用途 |
|------|-----|------|
| `fontFamilySans` | `SF Pro Text` | 正文、UI |
| `fontFamilyDisplay` | `SF Pro Display` | 大标题 |
| `fontFamilyMono` | `SF Mono` | 代码、日志 |
| `fontMonospace` | `SF Mono, Menlo, Monaco, Courier New, monospace` | 回退链 |

## 行高与字间距

| 名称 | 值 | 用途 |
|------|-----|------|
| `lineHeightTight` | 1.2 | 标题 |
| `lineHeightNormal` | 1.5 | 正文 |
| `lineHeightRelaxed` | 1.75 | 多行文本 |
| `letterSpacingTight` | -0.2 | 大标题 |
| `letterSpacingNormal` | 0 | 正文 |
| `letterSpacingWide` | 0.5 | 侧边栏 header |

## 窗口与布局尺寸

| 名称 | 值 | 用途 |
|------|-----|------|
| `windowDefaultWidth` | 1000 | 默认窗口宽度 |
| `windowDefaultHeight` | 700 | 默认窗口高度 |
| `windowMinWidth` | 700 | 最小宽度 |
| `windowMinHeight` | 500 | 最小高度 |

### 侧边栏

| 名称 | 值 | 用途 |
|------|-----|------|
| `sidebarMin` | 200 | 最小宽度 |
| `sidebarIdeal` | 240 | 理想宽度 |
| `sidebarMax` | 320 | 最大宽度 |
| `sidebarIconOnly` | 48 | 仅图标模式 |

### 响应式断点

| 名称 | 值 | 用途 |
|------|-----|------|
| `breakpointCompact` | 600 | 紧凑布局阈值 |
| `breakpointStandard` | 900 | 标准布局阈值 |

### 内容宽度

| 名称 | 值 | 用途 |
|------|-----|------|
| `maxContentWidth` | 680 | 一般页面内容最大宽度 |
| `maxFormContentWidth` | 760 | 设置页表单宽度 |
| `maxToolContentWidth` | 840 | 工具页网格宽度 |
| `contentWidthPadding` | 40 | `spacingXL * 2`，用于 `Math.min()` |

## 动画时长

| 名称 | 值 | 用途 |
|------|-----|------|
| `animationFast` | 150ms | hover、颜色过渡 |
| `animationNormal` | 300ms | Toast 滑入 |
| `animationSlow` | 500ms | 页面过渡 |

## 组件尺寸

| 名称 | 值 | 用途 |
|------|-----|------|
| `titleBarHeight` | 38 | 标题栏高度 |
| `titleBarButtonWidth` | 36 | 窗口控制按钮宽 |
| `titleBarButtonHeight` | 26 | 窗口控制按钮高 |
| `navItemHeight` | 32 | 侧边栏导航项高 |
| `navItemSpacing` | 2 | 导航项间距 |
| `iconSize` | 16 | 图标尺寸 |
| `indicatorWidth` | 3 | 选中指示器宽 |
| `labelWidthWide` | 120 | Config 组件标签宽 |
| `labelWidthNarrow` | 100 | 窄标签宽 |
| `logFilterBarHeight` | 44 | 日志过滤栏高 |
| `progressBarHeight` | 8 | 进度条高 |
| `resizeHandleSize` | 8 | 边缘拖拽区域 |
| `toastHeight` | 40 | Toast 高度 |

## Toast 时长

| 名称 | 值 |
|------|-----|
| `toastDuration` | 2000ms |
| `toastErrorDuration` | 3000ms |

## About 页面

| 名称 | 值 |
|------|-----|
| `aboutCardWidth` | 400 |
| `aboutCardHeight` | 320 |
| `aboutDividerWidth` | 300 |
