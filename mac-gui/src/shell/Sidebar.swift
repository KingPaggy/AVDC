// Sidebar.swift — SwiftUI 侧边栏视图（5 页导航）
// 通过 NSHostingView 嵌入 AppKit 侧边栏（方案 A 验证）
// 对齐 macOS 27 Golden Gate：彩色图标 + 选中高亮（docs-macOS27-09）
//
// 选中态实现说明：CLT（未装 Xcode）缺 SwiftUIMacros 宏插件，@State
// 无法编译。故状态提升到 SidebarView（NSObject），手动构造
// Binding<Int?> 驱动 List(selection:)，选中圆角高亮仍由系统渲染；
// 变更后重建 rootView 触发 SwiftUI 重新求值回显高亮。

import AppKit
import SwiftUI

@objc public final class SidebarView: NSObject {
    @objc public let view: NSView
    private var host: NSHostingView<SidebarContent>
    private var onSelectBlock: (@convention(block) (Int) -> Void)?
    private(set) var selectedIndex: Int = 0

    @objc public init(onSelect: @escaping @convention(block) (Int) -> Void) {
        onSelectBlock = onSelect
        // 占位 content 完成属性初始化（init 期不能引用 self 闭包）
        let placeholder = NSHostingView(rootView: SidebarContent(
            selection: .constant(nil as Int?)))
        view = placeholder
        host = placeholder
        super.init()
        rebuild()   // 换真实 binding，匹配当前 selectedIndex
    }

    // 依据当前 selectedIndex 重建 rootView，触发 SwiftUI 重新求值
    private func rebuild() {
        let selection = Binding<Int?>(
            get: { [weak self] in self?.selectedIndex },
            set: { [weak self] newValue in
                if let idx = newValue { self?.notify(idx) }
            })
        host.rootView = SidebarContent(selection: selection)
    }

    private func notify(_ idx: Int) {
        guard idx != selectedIndex else { return }
        selectedIndex = idx
        onSelectBlock?(idx)         // → AppDelegate 切页面
        rebuild()                   // 立即回显选中高亮
    }

    // AppKit 侧（菜单快捷键等）同步选中态到侧边栏高亮
    @objc public func setSelectedIndex(_ idx: Int) {
        guard idx != selectedIndex else { return }
        selectedIndex = idx
        rebuild()
    }
}

struct SidebarContent: View {
    var selection: Binding<Int?>

    // 5 页导航：每项独立强调色（docs-macOS27-09 §侧边栏）
    let items: [(name: String, icon: String, color: Color)] = [
        ("主页", "house.fill", .blue),
        ("设置", "gearshape.fill", .gray),
        ("工具", "wrench.and.screwdriver.fill", .orange),
        ("日志", "doc.text.fill", .purple),
        ("关于", "info.circle.fill", .green),
    ]

    var body: some View {
        List(selection: selection) {
            Section("AVDC") {
                ForEach(Array(items.enumerated()), id: \.offset) { idx, it in
                    Label {
                        Text(it.name)
                            .font(.system(size: 13))   // 中档 13pt（HIG 三档）
                    } icon: {
                        Image(systemName: it.icon)
                            .font(.system(size: 13, weight: .medium))
                            .foregroundStyle(it.color)
                    }
                    .padding(.vertical, 3)             // 行高约 28pt（中档）
                    .tag(idx)                         // 系统据此渲染选中高亮
                }
            }
        }
        .listStyle(.sidebar)
        // 玻璃边栏由系统提供（macOS 26+ 自动），不叠自定义背景
        // 选中圆角高亮由系统渲染（source list 选中态）
    }
}
