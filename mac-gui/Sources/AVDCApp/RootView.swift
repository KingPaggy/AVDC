import SwiftUI
import AVDCAppCore

// 根视图：NavigationSplitView（侧边栏 3 页导航 + 内容区）
// 侧边栏收敛为 主页/工具/日志：设置走 ⌘, 独立窗口，关于走 App 菜单
// @Observable 单例 + @Bindable（CLT 无 @State 宏，见方案 §2）
struct RootView: View {
    @Bindable var model = AppModel.shared

    var body: some View {
        NavigationSplitView {
            SidebarView(model: model)
                .navigationSplitViewColumnWidth(min: 180, ideal: 220,
                                                max: 280)
        } detail: {
            detail
        }
    }

    @ViewBuilder
    private var detail: some View {
        switch model.page {
        case .home:
            HomeView(model: model)
        case .tools:
            ToolsView(model: model)
        case .log:
            LogView(model: model)
        }
    }
}

// 侧边栏：3 页导航 + 彩色图标（macOS 27 彩色图标回归）
// Golden Gate 贴边由系统渲染，不叠任何背景
struct SidebarView: View {
    @Bindable var model: AppModel

    var body: some View {
        List(Page.allCases, selection: $model.page) { page in
            Label(page.title, systemImage: page.icon)
                .listItemTint(.fixed(page.tint))
                .tag(page)
        }
        .listStyle(.sidebar)
        .navigationTitle(AppInfo.name)
    }
}
