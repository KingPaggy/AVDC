import SwiftUI
import AVDCAppCore

// 设计令牌：颜色 / 间距 / 玻璃参数的唯一来源
// 依据 HIG（语义色、8pt 网格、20-8-6 规则）与 macOS 27 收敛圆角
// 完整规格见 docs/report-2026-09-21-1016-macGUI-官方设计标准对齐优化方案.md

// MARK: - 间距（HIG 8pt 网格）

enum Metric {
    static let item: CGFloat = 8         // 标签↔控件 / 工具栏项间距
    static let group: CGFloat = 16       // 分组内边距 / 徽章间距
    static let gutter: CGFloat = 20      // 窗口内容外边距（HIG）
}

// MARK: - 页面映射（Core 保持无 SwiftUI 依赖，故放视图层）

extension Page {
    /// 侧边栏彩色图标 tint（macOS 27 彩色图标回归）
    var tint: Color {
        switch self {
        case .home: return .blue
        case .tools: return .orange
        case .log: return .teal
        }
    }

    /// 显示菜单快捷键 ⌘1–⌘3
    var shortcut: KeyEquivalent {
        switch self {
        case .home: return KeyEquivalent("1")
        case .tools: return KeyEquivalent("2")
        case .log: return KeyEquivalent("3")
        }
    }
}

// MARK: - 语义色
// 状态色用系统语义色（随浅/深色与提高对比度自适应），不用 .green/.red 字面量

enum Palette {
    static let ok = Color(nsColor: .systemGreen)
    static let fail = Color(nsColor: .systemRed)
    static let warn = Color(nsColor: .systemOrange)
    static let info = Color(nsColor: .secondaryLabelColor)

    /// 提高对比度时描边改用 label 色（无障碍降级）
    static func border(_ contrast: ColorSchemeContrast) -> Color {
        contrast == .increased
            ? Color(nsColor: .labelColor) : Color(nsColor: .separatorColor)
    }
}

// MARK: - 玻璃
// 只用于导航层悬浮元素，且只用 .regular（clear 需媒体背景 + 暗层三条件）
// 屏幕玻璃层 ≤ 12；就近玻璃必须同容器（分组共享采样，8 层 2.8ms → 0.6ms）

enum GlassStyle {
    static let containerSpacing: CGFloat = 12
}
