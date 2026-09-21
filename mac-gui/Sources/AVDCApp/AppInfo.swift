import AppKit

// 版本与「关于」信息的唯一来源
// 无 bundle（决策 4）→ About 面板靠 orderFrontStandardAboutPanel(options:)
// 程序化传参，不读 Info.plist；最低系统由链接期 minos = 26.0 承担
enum AppInfo {
    static let name = "AVDC"
    static let version = "0.3.0"       // 与 CLI --version 对齐
    static let build = "2026.09"
    static let copyright = "© 2026 AVDC · AV Data Capture"

    static let credits = NSAttributedString(
        string: """
        AV Data Capture — 抓取影片元数据并整理本地视频文件，
        输出供 Emby / Kodi / Plex 使用。
        """,
        attributes: [
            .font: NSFont.systemFont(ofSize: NSFont.smallSystemFontSize),
            .foregroundColor: NSColor.secondaryLabelColor,
        ])

    /// 系统 About 面板（App 菜单项）
    @MainActor
    static func showAboutPanel() {
        NSApplication.shared.orderFrontStandardAboutPanel(options: [
            .applicationName: name,
            .applicationVersion: version,
            .version: build,
            .credits: credits,
        ])
    }
}
