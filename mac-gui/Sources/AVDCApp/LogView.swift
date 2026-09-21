import SwiftUI
import AVDCAppCore

// 日志页：级别过滤 + 搜索 + 虚拟化列表 + 空状态
// 过滤/导出/清空进工具栏，内容区只放日志行
struct LogView: View {
    @Bindable var model: AppModel
    @FocusState private var searchFocused: Bool   // ⌘F 聚焦搜索框

    var body: some View {
        Group {
            if filteredLogs.isEmpty {
                ContentUnavailableView {
                    Label(model.logs.isEmpty ? "暂无日志" : "无匹配日志",
                          systemImage: "doc.text")
                } description: {
                    Text(model.logs.isEmpty
                         ? "开始处理后会在此实时显示日志。"
                         : "换个关键字或清除过滤条件。")
                }
            } else {
                List(filteredLogs) { entry in
                    row(entry)
                }
                .listStyle(.inset)
                .textSelection(.enabled)
            }
        }
        .searchable(text: $model.logQuery, placement: .toolbar,
                    prompt: "搜索日志")
        .searchFocused($searchFocused)
        .onChange(of: model.searchFocusRequest) { searchFocused = true }
        .navigationTitle("日志")
        .navigationSubtitle("\(filteredLogs.count) 条")
        .toolbar { toolbar }
        .confirmationDialog("清空全部日志？", isPresented: $model.pendingClearLogs) {
            Button("清空", role: .destructive) { model.logs.removeAll() }
            Button("取消", role: .cancel) {}
        } message: {
            Text("共 \(model.logs.count) 条日志将被删除，不可撤销。")
        }
    }

    @ToolbarContentBuilder
    private var toolbar: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Picker("级别", selection: $model.logFilter) {
                Text("全部").tag(LogLevel?.none)
                ForEach(LogLevel.allCases, id: \.self) { level in
                    Text(level.label).tag(LogLevel?.some(level))
                }
            }
            .pickerStyle(.menu)
            .help("按级别过滤")
        }
        ToolbarItem(placement: .primaryAction) {
            Button("导出…") { AVDCActions.exportLogs() }
                .disabled(model.logs.isEmpty)
                .help("导出日志为文本文件（⌘E）")
        }
        ToolbarItem(placement: .primaryAction) {
            Button("清空") { model.pendingClearLogs = true }
                .disabled(model.logs.isEmpty)
                .help("清空当前日志")
        }
    }

    // 日志行：级别点 + 时间 + 文本；VoiceOver 合并朗读
    private func row(_ entry: LogEntry) -> some View {
        HStack(alignment: .top, spacing: Metric.item) {
            Circle()
                .fill(levelColor(entry.level))
                .frame(width: 8, height: 8)
                .padding(.top, 5)
                .accessibilityHidden(true)
            Text(AVDCActions.timeString(entry.timestamp))
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.tertiary)
            Text(entry.message)
                .font(.system(.caption))
                .foregroundStyle(entry.level == .error
                                 ? AnyShapeStyle(Palette.fail)
                                 : AnyShapeStyle(.primary))
        }
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(entry.level.label) "
                            + "\(AVDCActions.timeString(entry.timestamp)) "
                            + entry.message)
    }

    // 过滤后日志（新→旧）
    private var filteredLogs: [LogEntry] {
        var result = model.logs.reversed() as [LogEntry]
        if let level = model.logFilter {
            result = result.filter { $0.level == level }
        }
        let q = model.logQuery.trimmingCharacters(in: .whitespaces)
        if !q.isEmpty {
            result = result.filter {
                $0.message.localizedCaseInsensitiveContains(q)
            }
        }
        return result
    }

    private func levelColor(_ level: LogLevel) -> Color {
        switch level {
        case .info: return Palette.info
        case .warn: return Palette.warn
        case .error: return Palette.fail
        }
    }
}
