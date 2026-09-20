// InfoBar.swift — 内容区顶部信息条（SwiftUI 原生文字层）
// 页面标题文字 + 全屏玻璃按钮由 SwiftUI 承载；
// ImGui 仅绘制页面内容区。桥接模式复用 SidebarView
// （NSObject 包装 + Block 回调；CLT 无宏插件故不用 @State，
// 参数化重建 rootView 驱动刷新）。

import AppKit
import SwiftUI

@objc public final class InfoBarView: NSObject {
    @objc public let view: NSView
    private var host: NSHostingView<InfoBarContent>
    private let onToggleFullScreenBlock: (@convention(block) () -> Void)?

    @objc public init(onToggleFullScreen: @escaping @convention(block) () -> Void) {
        onToggleFullScreenBlock = onToggleFullScreen
        // 占位 content 完成属性初始化（init 期不能引用 self 闭包）
        let placeholder = NSHostingView(rootView: InfoBarContent(
            title: "", onToggleFullScreen: nil))
        view = placeholder
        host = placeholder
        super.init()
    }

    // AppKit 侧刷新信息条（页面切换时调用）
    @objc public func setTitle(_ title: String) {
        host.rootView = InfoBarContent(
            title: title,
            onToggleFullScreen: { [weak self] in
                self?.onToggleFullScreenBlock?() })
    }
}

struct InfoBarContent: View {
    let title: String
    let onToggleFullScreen: (() -> Void)?

    var body: some View {
        HStack(spacing: 10) {
            Text(title)
                .font(.system(size: 15, weight: .medium))
                .lineLimit(1)
            Spacer(minLength: 10)
            if let onToggleFullScreen {
                Button(action: onToggleFullScreen) {
                    Image(systemName: "arrow.up.left.and.arrow.down.right")
                        .font(.system(size: 12, weight: .medium))
                        .frame(width: 22, height: 22)
                        .glassEffect(.regular.interactive())   // 液态玻璃
                }
                .buttonStyle(.plain)
                .help("切换全屏")
            }
        }
        .padding(.horizontal, 14)
        .padding(.top, 6)      // 内容上移落入标题栏行（0–28pt）
        .frame(height: 40)     // 底部留空：与内容区拉开距离
        .background(Color(nsColor: .controlBackgroundColor))
        .overlay(alignment: .bottom) {
            Rectangle()
                .fill(Color(nsColor: .separatorColor))
                .frame(height: 1)
        }
        // InfoBar 有意落入标题栏行（方案 D），无视顶部安全区；
        // macOS 26 对透明标题栏窗口仍上报 32pt 安全区，会把内容
        // 推出 40pt hosting view 并被更高 z 序的 MTKView 遮住
        .ignoresSafeArea(.container, edges: .top)
    }
}
