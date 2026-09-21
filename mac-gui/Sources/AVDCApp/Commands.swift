import SwiftUI
import AVDCAppCore

// 菜单栏：按 HIG 结构组织，快捷键与工具栏按钮同源
// App → 文件 → 编辑 → 显示 → 处理 → 窗口 → 帮助
struct AVDCCommands: Commands {
    private var model: AppModel { .shared }

    var body: some Commands {
        // ---- App 菜单 ----
        // 关于走系统面板；本工具无「新建」，移除默认项
        CommandGroup(replacing: .appInfo) {
            Button("关于 \(AppInfo.name)") { AppInfo.showAboutPanel() }
        }
        CommandGroup(replacing: .newItem) {}

        // ---- 文件 ----
        CommandGroup(after: .newItem) {
            Button("选择影片目录…") { AVDCActions.chooseInputDirectory() }
                .keyboardShortcut("o", modifiers: .command)
            Button("导出日志…") { AVDCActions.exportLogs() }
                .keyboardShortcut("e", modifiers: .command)
                .disabled(model.logs.isEmpty)
        }

        // ---- 编辑（查找 ⌘F：聚焦当前页搜索框）----
        CommandGroup(after: .textEditing) {
            Divider()
            Menu("查找") {
                Button("查找…") {
                    // 主窗口与设置窗口各自监听，只有键窗口的页面聚焦
                    model.searchFocusRequest += 1
                    model.settings.searchFocusRequest += 1
                }
                .keyboardShortcut("f", modifiers: .command)
            }
        }

        // ---- 显示（切页 ⌘1–⌘3，设置 ⌘, 由系统 Settings 场景提供）----
        CommandGroup(after: .toolbar) {
            Divider()
            ForEach(Page.allCases) { page in
                Button(page.title) { model.page = page }
                    .keyboardShortcut(page.shortcut, modifiers: .command)
            }
        }

        // 全屏 ⌃⌘F（SwiftUI Window 场景默认不生成该项；HIG 放 View 菜单）
        CommandGroup(after: .toolbar) {
            Button("进入全屏") { NSApp.keyWindow?.toggleFullScreen(nil) }
                .keyboardShortcut("f", modifiers: [.control, .command])
        }

        // 侧边栏 ⌘⌥S：接管系统项（SwiftUI 会把系统 Toggle Sidebar
        // 错放到 Help 末尾），用模型状态实现显隐。标题用静态文案，
        // 不依赖 Commands 对状态的观察（动作读模型当前值，恒准确）
        CommandGroup(replacing: .sidebar) {
            Button("切换侧边栏") { model.sidebarHidden.toggle() }
                .keyboardShortcut("s", modifiers: [.command, .option])
        }

        // ---- 处理 ----
        CommandMenu("处理") {
            Button("开始处理") { model.startProcessing() }
                .keyboardShortcut("r", modifiers: .command)
                .disabled(model.isRunning || model.inputDir.isEmpty)
            Button("停止") { model.stopProcessing() }
                .keyboardShortcut(".", modifiers: .command)
                .disabled(!model.isRunning)
        }
    }
}
