import SwiftUI
import AppKit
import AVDCAppCore

// 主页：输入 / 处理模式 / 进度 / 结果列表
// 对齐 QML HomePage（输入目录、排除文件夹、刮削/整理、进度、徽章）
// 原生 SwiftUI 控件（TextField/Picker/ProgressView/List）
struct HomeView: View {
    @Bindable var model: AppModel

    var body: some View {
        List {
            // ---- 输入 ----
            Section("输入") {
                LabeledContent("输入目录") {
                    HStack(spacing: 8) {
                        TextField("选择影片目录", text: $model.inputDir)
                            .textFieldStyle(.roundedBorder)
                        Button("浏览…") { chooseDirectory() }
                    }
                }
                LabeledContent("排除文件夹") {
                    TextField("逗号分隔的目录名", text: $model.escapeFolders)
                        .textFieldStyle(.roundedBorder)
                }
            }

            // ---- 处理模式 ----
            Section("处理模式") {
                Picker("模式", selection: $model.mode) {
                    Text("刮削模式").tag(1)
                    Text("整理模式").tag(2)
                }
                .pickerStyle(.segmented)

                Button {
                    if model.isRunning {
                        model.stopProcessing()
                    } else {
                        model.startProcessing()
                    }
                } label: {
                    if model.isRunning {
                        Label("停止", systemImage: "stop.fill")
                            .frame(maxWidth: .infinity)
                    } else {
                        Label("开始处理", systemImage: "play.fill")
                            .frame(maxWidth: .infinity)
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(model.inputDir.isEmpty)
            }

            // ---- 进度 ----
            Section("进度") {
                ProgressView(value: progress, total: 1)
                if !model.statusText.isEmpty {
                    Text(model.statusText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
                HStack(spacing: 18) {
                    Label("成功: \(model.success)",
                          systemImage: "checkmark.circle.fill")
                        .foregroundStyle(.green)
                    Label("失败: \(model.fail)",
                          systemImage: "xmark.circle.fill")
                        .foregroundStyle(.red)
                    Label("总数: \(model.total)",
                          systemImage: "number.circle.fill")
                        .foregroundStyle(.secondary)
                }
                .font(.caption)
            }

            // ---- 结果列表 ----
            if !model.results.isEmpty {
                Section("结果") {
                    ForEach(model.results.reversed()) { r in
                        HStack(spacing: 8) {
                            Image(systemName: statusIcon(r.status))
                                .foregroundStyle(statusColor(r.status))
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
                    }
                }
            }
        }
        .listStyle(.inset)
        .navigationTitle("主页")
    }

    // 进度 0..1
    private var progress: Double {
        guard model.total > 0 else { return 0 }
        return min(Double(model.current) / Double(model.total), 1)
    }

    // 结果状态图标/颜色
    private func statusIcon(_ s: Int) -> String {
        switch s {
        case 1: return "checkmark.circle"
        case 2: return "xmark.circle"
        default: return "circle"
        }
    }

    private func statusColor(_ s: Int) -> Color {
        switch s {
        case 1: return .green
        case 2: return .red
        default: return .secondary
        }
    }

    // 目录选择（NSOpenPanel，无需 SwiftUI 呈现状态）
    private func chooseDirectory() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        if !model.inputDir.isEmpty {
            panel.directoryURL = URL(fileURLWithPath: model.inputDir)
        }
        panel.begin { resp in
            if resp == .OK, let url = panel.url {
                model.inputDir = url.path
            }
        }
    }
}
