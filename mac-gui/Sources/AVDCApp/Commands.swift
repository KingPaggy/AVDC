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

        // ---- 显示（切页 ⌘1–⌘3，设置 ⌘, 由系统 Settings 场景提供）----
        CommandGroup(after: .sidebar) {
            Divider()
            ForEach(Page.allCases) { page in
                Button(page.title) { model.page = page }
                    .keyboardShortcut(page.shortcut, modifiers: .command)
            }
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
