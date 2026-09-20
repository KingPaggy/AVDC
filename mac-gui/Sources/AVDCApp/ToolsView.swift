import SwiftUI
import AVDCAppCore

// 工具页：工具卡片网格（对齐 QML ToolsPage，均按现状「待实现」）
struct ToolsView: View {
    @Bindable var model: AppModel

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                toolSection(title: "文件工具", tools: Self.fileTools)
                toolSection(title: "媒体库工具", tools: Self.libraryTools)
            }
            .padding(20)
        }
        .navigationTitle("工具")
        .alert("提示", isPresented: alertBinding) {
            Button("好", role: .cancel) {}
        } message: {
            Text(model.toolMessage ?? "")
        }
    }

    private var alertBinding: Binding<Bool> {
        Binding(
            get: { model.toolMessage != nil },
            set: { if !$0 { model.toolMessage = nil } })
    }

    // ---- 工具定义（8 个，对照 QML）----
    struct ToolItem: Identifiable {
        let id = UUID()
        let icon: String
        let title: String
        let desc: String
    }

    static let fileTools: [ToolItem] = [
        ToolItem(icon: "pencil.and.outline", title: "批量重命名",
                 desc: "按命名规则批量重命名影片文件"),
        ToolItem(icon: "crop", title: "封面裁剪",
                 desc: "自动裁剪 Poster 和 Thumb 封面图"),
        ToolItem(icon: "drop.halffull", title: "水印处理",
                 desc: "批量添加或去除封面水印"),
        ToolItem(icon: "arrow.triangle.2.circlepath", title: "格式转换",
                 desc: "视频格式批量转换（MP4 / MKV）"),
    ]

    static let libraryTools: [ToolItem] = [
        ToolItem(icon: "server.rack", title: "Emby 同步",
                 desc: "同步元数据到 Emby 媒体库"),
        ToolItem(icon: "doc.badge.gearshape", title: "NFO 生成器",
                 desc: "手动生成或修复 NFO 元数据文件"),
        ToolItem(icon: "square.and.pencil", title: "元数据编辑",
                 desc: "手动编辑影片元数据信息"),
        ToolItem(icon: "copy.on.copy", title: "重复检测",
                 desc: "扫描并去重重复的媒体文件"),
    ]

    // ---- 分组渲染 ----
    private func toolSection(title: String, tools: [ToolItem]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(title)
                .font(.headline)
            LazyVGrid(columns: [GridItem(.adaptive(minimum: 260),
                                         spacing: 14)], spacing: 14) {
                ForEach(tools) { tool in
                    ToolCardView(tool: tool) {
                        model.toolMessage = "\(tool.title)（待实现）"
                    }
                }
            }
        }
    }
}

// 工具卡片
struct ToolCardView: View {
    let tool: ToolsView.ToolItem
    let onOpen: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(alignment: .top) {
                Image(systemName: tool.icon)
                    .font(.system(size: 18, weight: .medium))
                    .foregroundStyle(.tint)
                Spacer()
                Button("打开") { onOpen() }
                    .controlSize(.small)
            }
            Text(tool.title)
                .font(.headline)
            Text(tool.desc)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 10)
            .fill(Color(nsColor: .controlBackgroundColor)))
        .overlay(RoundedRectangle(cornerRadius: 10)
            .stroke(Color(nsColor: .separatorColor)))
    }
}
