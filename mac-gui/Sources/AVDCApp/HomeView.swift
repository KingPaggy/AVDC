import SwiftUI
import AVDCAppCore

// 主页：输入 / 处理模式 / 进度 / 结果
// 表单用 HIG grouped 形态；主操作（开始/停止）放工具栏，内容区只放字段
struct HomeView: View {
    @Bindable var model: AppModel
    @FocusState private var inputFocused: Bool
    @Namespace private var hudNamespace
    // 无障碍降级：减透明度→去玻璃改用材质；减动效→不做形变/淡入
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @Environment(\.colorSchemeContrast) private var contrast

    var body: some View {
        Form {
            Section("输入") {
                LabeledContent("输入目录") {
                    HStack(spacing: Metric.item) {
                        TextField("选择影片目录", text: $model.inputDir)
                            .textFieldStyle(.roundedBorder)
                            .focused($inputFocused)
                            .onSubmit { toggleProcessing() }
                        Button("浏览…") { AVDCActions.chooseInputDirectory() }
                            .help("选择影片目录（⌘O）")
                    }
                }
                LabeledContent("排除文件夹") {
                    TextField("逗号分隔的目录名", text: $model.escapeFolders)
                        .textFieldStyle(.roundedBorder)
                }
            }

            Section("处理模式") {
                Picker("模式", selection: $model.mode) {
                    Text("刮削模式").tag(1)
                    Text("整理模式").tag(2)
                }
                .pickerStyle(.segmented)
            }

            Section("进度") {
                ProgressView(value: progress, total: 1)
                    .accessibilityLabel("处理进度")
                    .accessibilityValue("\(model.current) / \(model.total)")
                if !model.statusText.isEmpty {
                    Text(model.statusText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                HStack(spacing: Metric.group) {
                    Label("成功: \(model.success)",
                          systemImage: "checkmark.circle.fill")
                        .foregroundStyle(Palette.ok)
                    Label("失败: \(model.fail)",
                          systemImage: "xmark.circle.fill")
                        .foregroundStyle(Palette.fail)
                    Label("总数: \(model.total)",
                          systemImage: "number.circle.fill")
                        .foregroundStyle(Palette.info)
                }
                .font(.caption)
            }

            Section("结果") {
                if model.results.isEmpty {
                    Text("尚无结果：选择目录后开始处理。")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(model.results) { r in
                        resultRow(r)
                    }
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("主页")
        .navigationSubtitle(subtitle)
        .toolbar { toolbar }
        .overlay(alignment: .bottom) { progressHUD }
        .animation(reduceMotion ? nil : .easeOut(duration: 0.2),
                   value: model.isRunning)
    }

    // MARK: - 进度 HUD（唯一的自绘玻璃：浮在内容上方的导航层元素）

    @ViewBuilder
    private var progressHUD: some View {
        if model.isRunning {
            GlassEffectContainer(spacing: GlassStyle.containerSpacing) {
                HStack(spacing: Metric.item) {
                    ProgressView(value: progress, total: 1)
                        .frame(width: 120)
                    Text("\(model.current) / \(model.total)")
                        .font(.callout)
                        .monospacedDigit()
                }
                .padding(.horizontal, Metric.group)
                .padding(.vertical, Metric.item)
                .modifier(HUDChrome(reduceTransparency: reduceTransparency,
                                    contrast: contrast))
                .glassEffectID("progressHUD", in: hudNamespace)
            }
            .padding(.bottom, Metric.gutter)
            .transition(.opacity)
            .accessibilityElement(children: .combine)
            .accessibilityLabel("\u{6b63}\u{5728}\u{5904}\u{7406}"
                                + "\(model.current) / \(model.total)")
        }
    }

    // 进度 0..1
    private var progress: Double {
        guard model.total > 0 else { return 0 }
        return min(Double(model.current) / Double(model.total), 1)
    }

    private var subtitle: String {
        model.isRunning || model.total > 0
            ? "\(model.current) / \(model.total)" : ""
    }

    @ToolbarContentBuilder
    private var toolbar: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button { toggleProcessing() } label: {
                Label(model.isRunning ? "停止" : "开始处理",
                      systemImage: model.isRunning ? "stop.fill"
                                                   : "play.fill")
            }
            .buttonStyle(.borderedProminent)
            .disabled(!model.isRunning && model.inputDir.isEmpty)
            .help(model.isRunning ? "停止处理（⌘.）" : "开始处理（⌘R）")
        }
    }

    private func toggleProcessing() {
        if model.isRunning {
            model.stopProcessing()
        } else {
            model.startProcessing()
        }
    }

    // 结果行：图标 + 番号 + 文件 + 详情，VoiceOver 合并朗读
    private func resultRow(_ r: HomeFileResult) -> some View {
        HStack(spacing: Metric.item) {
            Image(systemName: statusIcon(r.status))
                .foregroundStyle(statusColor(r.status))
                .accessibilityHidden(true)
            Text(r.number)
                .font(.system(.body, design: .monospaced))
            Text(r.file)
                .foregroundStyle(.secondary)
                .lineLimit(1)
            Spacer()
            Text(r.detail)
                .foregroundStyle(.tertiary)
                .lineLimit(1)
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(r.number) \(statusText(r.status)) \(r.detail)")
    }

    private func statusIcon(_ s: Int) -> String {
        switch s {
        case 1: return "checkmark.circle"
        case 2: return "xmark.circle"
        default: return "circle"
        }
    }

    private func statusColor(_ s: Int) -> Color {
        switch s {
        case 1: return Palette.ok
        case 2: return Palette.fail
        default: return Palette.info
        }
    }

    private func statusText(_ s: Int) -> String {
        switch s {
        case 1: return "成功"
        case 2: return "失败"
        default: return "待处理"
        }
    }
}

// 进度 HUD 外观：玻璃只用于导航层悬浮元素；
// 减透明度 → 降级为 .regularMaterial（不依赖玻璃）；提高对比度 → 加描边
private struct HUDChrome: ViewModifier {
    let reduceTransparency: Bool
    let contrast: ColorSchemeContrast

    func body(content: Content) -> some View {
        content
            .glassEffect(reduceTransparency ? Glass.identity
                                            : .regular.tint(.accentColor),
                         in: .capsule)
            .background(reduceTransparency ? AnyShapeStyle(.regularMaterial)
                                           : AnyShapeStyle(.clear),
                        in: .capsule)
            .overlay(Capsule().strokeBorder(Palette.border(contrast)))
    }
}
