import SwiftUI
import AVDCAppCore

@main
struct AVDCApp: App {
    // 无 bundle → 需 AppDelegate 把进程拉回前台（Dock 图标/菜单栏/快捷键前提）
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        // 单窗口工具（无「新建窗口」语义）；统一紧凑工具栏条
        Window("AVDC", id: "main") {
            RootView()
        }
        .defaultSize(width: 1080, height: 720)
        .windowResizability(.contentMinSize)
        .windowToolbarStyle(.unifiedCompact)
        .commands { AVDCCommands() }

        // 设置：独立偏好窗口（⌘,），系统自带 preference 工具栏外观
        Settings {
            SettingsScene(state: AppModel.shared.settings,
                          bridge: AppModel.shared.bridge)
        }
    }
}
