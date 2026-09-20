import SwiftUI
import AVDCAppCore

// 根视图：NavigationSplitView（侧边栏 5 页导航 + 内容区）
// @Observable 单例 + @Bindable（CLT 无 @State 宏，见方案 §2.2）
struct RootView: View {
    @Bindable var model = AppModel.shared

    var body: some View {
        NavigationSplitView {
            SidebarView(model: model)
                .navigationSplitViewColumnWidth(min: 160, ideal: 200)
        } detail: {
            detail
        }
    }

    @ViewBuilder
    private var detail: some View {
        switch model.page {
        case .home:
            HomeView(model: model)
        case .settings:
            SettingsView(settings: model.settings, bridge: model.bridge)
        case .tools:
            ToolsView(model: model)
        case .log:
            LogView(model: model)
        case .about:
            AboutView()
        }
    }
}

// 侧边栏：5 页导航 + 彩色图标（对齐 QML MacOSSidebar）
struct SidebarView: View {
    @Bindable var model: AppModel

    var body: some View {
        List(Page.allCases, selection: $model.page) { page in
            Label(page.title, systemImage: page.icon)
                .tag(page)
        }
        .listStyle(.sidebar)
        .navigationTitle("AVDC")
    }
}
