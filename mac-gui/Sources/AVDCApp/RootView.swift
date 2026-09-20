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
        default:
            PagePlaceholder(page: model.page)
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

// 未实现页面占位（阶段 1′-3′ 填充）
struct PagePlaceholder: View {
    let page: Page

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: page.icon)
                .font(.system(size: 40, weight: .light))
                .foregroundStyle(.tertiary)
            Text(page.title)
                .font(.system(size: 24, weight: .medium))
            Text("此页面将在后续阶段实现")
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
