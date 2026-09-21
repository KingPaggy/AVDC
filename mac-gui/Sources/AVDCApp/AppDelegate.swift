import AppKit

// 无 bundle（决策 4）时 LaunchServices 把进程登记为 BackgroundOnly：
//   → 无 Dock 图标、菜单栏不归属本进程、所有菜单键等同（⌘R/⌘./⌘1–3…）
//     乃至系统 Edit 菜单的 ⌘C/⌘V/⌘A 都不派发
// 修复：启动时显式改回 .regular 并激活为前台
// 诊断依据：docs/report-2026-09-21-1036-macGUI-前台激活与快捷键修复方案.md
final class AppDelegate: NSObject, NSApplicationDelegate {

    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApplication.shared.setActivationPolicy(.regular)
        NSApplication.shared.activate()

        // SwiftUI 会把系统 Toggle Sidebar 残留到 Help 菜单（无快捷键的
        // 孤儿项）；我们的 ⌘⌥S 已在 View 菜单，这里移除残留
        if let help = NSApp.mainMenu?.item(withTitle: "Help")?.submenu {
            for item in help.items
            where item.action == #selector(NSSplitViewController
                .toggleSidebar(_:)) {
                help.removeItem(item)
            }
        }

        // 调试钩子：AVDC_DUMP_MENU=1 打印菜单树（含快捷键）后退出
        // 用途：改动快捷键后核对键位归属与冲突
        if ProcessInfo.processInfo.environment["AVDC_DUMP_MENU"] != nil {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                Self.dumpMainMenu()
                exit(0)
            }
        }
    }

    // 单窗口工具：关掉最后一个窗口即退出
    func applicationShouldTerminateAfterLastWindowClosed(
        _ sender: NSApplication) -> Bool { true }

    // ---- 菜单转储（调试用）----
    static func dumpMainMenu() {
        func walk(_ menu: NSMenu?, _ depth: Int) {
            guard let menu else { return }
            let pad = String(repeating: "  ", count: depth)
            for (i, item) in menu.items.enumerated() {
                if item.isSeparatorItem { continue }
                var key = ""
                if !item.keyEquivalent.isEmpty {
                    var mods = ""
                    let mask = item.keyEquivalentModifierMask
                    if mask.contains(.command) { mods += "⌘" }
                    if mask.contains(.shift) { mods += "⇧" }
                    if mask.contains(.option) { mods += "⌥" }
                    if mask.contains(.control) { mods += "⌃" }
                    key = " [\(mods.uppercased()) \(item.keyEquivalent)]"
                }
                let state = item.isEnabled ? "" : " (disabled)"
                print("\(pad)\(menu.title) #\(i + 1) \(item.title)"
                      + "\(key)\(state)")
                walk(item.submenu, depth + 1)
            }
        }
        walk(NSApp.mainMenu, 0)
        print("--- activationPolicy=\(NSApp.activationPolicy().rawValue)"
              + " frontmost=\(NSApp.isActive)")
    }
}
