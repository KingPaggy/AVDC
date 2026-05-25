// Theme.qml — Apple HIG 平台无关主题单例
// 语义化颜色自动适配 Light/Dark Mode，8pt 网格间距，Apple HIG 字号层级
pragma Singleton

import QtQuick 2.15

Singleton {
    id: theme

    // ===== 系统调色板（自动 Light/Dark Mode） =====
    SystemPalette { id: sysPal }

    readonly property bool isDark: sysPal.window === "black" || sysPal.window.r < 0.5

    // ===== 文字颜色 =====
    readonly property color textColor:       isDark ? "#F5F5F7" : "#1D1D1F"   // Primary
    readonly property color secondaryText:   isDark ? "#98989D" : "#86868B"   // Secondary
    readonly property color tertiaryText:    isDark ? "#747476" : "#BFBFBF"   // Tertiary

    // ===== 语义颜色 =====
    readonly property color accentColor:     isDark ? "#0A84FF" : "#007AFF"   // Blue / 强调
    readonly property color errorColor:      isDark ? "#FF453A" : "#FF3B30"   // Red / 错误
    readonly property color successColor:    isDark ? "#30D158" : "#34C759"   // Green / 成功
    readonly property color warningColor:    isDark ? "#FF9F0A" : "#FF9500"   // Orange / 警告
    readonly property color infoColor:       isDark ? "#64D2FF" : "#5AC8FA"   // Cyan / 信息
    readonly property color purpleColor:     isDark ? "#BF5AF2" : "#AF52DE"
    readonly property color pinkColor:       isDark ? "#FF375F" : "#FF2D55"
    readonly property color mintColor:       isDark ? "#66E0D8" : "#00C7BE"
    readonly property color indigoColor:     isDark ? "#5E5CE6" : "#5856D6"
    readonly property color yellowColor:     isDark ? "#FFD60A" : "#FFCC00"
    readonly property color brownColor:      isDark ? "#AC8E68" : "#A2845E"

    // ===== 背景颜色 =====
    readonly property color backgroundColor:  isDark ? "#1E1E1E" : "#FFFFFF"   // 页面背景
    readonly property color sidebarBg:        isDark ? "#2D2D2D" : "#F5F5F7"   // 侧边栏背景
    readonly property color cardBg:           isDark ? "#2D2D2D" : "#F5F5F7"   // 卡片背景
    readonly property color inputBg:          isDark ? "#3A3A3C" : "#FFFFFF"   // 输入框背景
    readonly property color separatorColor:   isDark ? "#424245" : "#D1D1D6"   // 分隔线

    // ===== 交互颜色 =====
    readonly property color hoverBg:          isDark ? "#3A3A3C" : "#E5E5EA"   // 悬停背景
    readonly property color pressedBg:        isDark ? "#48484A" : "#D1D1D6"   // 按下背景
    readonly property color focusBorder:      accentColor                       // 聚焦边框

    // ===== 间距（8pt 网格） =====
    readonly property int spacingXS:  4    // 紧密相关（图标与文字）
    readonly property int spacingSM:  8    // 同组控件（Label + Input）
    readonly property int spacingMD:  12   // 卡片内边距
    readonly property int spacingLG:  16   // 功能组之间
    readonly property int spacingXL:  20   // 页面边距
    readonly property int spacingXXL: 24   // 大区块之间
    readonly property int spacingXXXL: 32  // 页面级分隔

    // ===== 圆角 =====
    readonly property int radiusSM: 4    // 小按钮、标签
    readonly property int radiusMD: 6    // 输入框
    readonly property int radiusLG: 8    // 列表项、卡片
    readonly property int radiusXL: 12   // 弹窗、Sheet

    // ===== 字号层级（Apple HIG） =====
    readonly property int fontTitle:       16  // 窗口标题 — Semibold
    readonly property int fontHeading:     13  // 章节标题 — Semibold
    readonly property int fontBody:        13  // 正文 — Regular
    readonly property int fontCaption:     11  // 标签/说明 — Regular
    readonly property int fontMini:        10  // 辅助文字 — Regular
    readonly property int fontSidebarHeader: 12 // 侧边栏分组 — Semibold
    readonly property int fontStat:        28  // 大数字 — Bold
    readonly property int fontLargeTitle:  34  // 大型页面标题
    readonly property int fontPageTitle:   28  // 页面标题

    // ===== 侧边栏宽度 =====
    readonly property int sidebarMin:   200
    readonly property int sidebarIdeal: 240
    readonly property int sidebarMax:   320
    readonly property int sidebarIconOnly: 48

    // ===== 窗口规格（管理类应用） =====
    readonly property int windowDefaultWidth:  1000
    readonly property int windowDefaultHeight: 700
    readonly property int windowMinWidth:      700
    readonly property int windowMinHeight:     500

    // ===== 响应式断点 =====
    readonly property int breakpointCompact: 600   // < 600: 折叠侧边栏
    readonly property int breakpointStandard: 900  // 600-900: 标准布局
    // > 900: 扩展模式

    // ===== 动画时长 =====
    readonly property int animationFast: 150     // 微交互（按钮 hover）
    readonly property int animationNormal: 300   // 状态变化（Toast、面板切换）
    readonly property int animationSlow: 500     // 布局动画
}
