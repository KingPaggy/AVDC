import SwiftUI
import AppKit
import AVDCAppCore

// 日志页：级别过滤 + 实时日志列表 + 清空/导出
// 数据来自 AppModel.logs（Home 处理过程实时追加）
struct LogView: View {
    @Bindable var model: AppModel

    var body: some View {
        VStack(spacing: 0) {
            filterBar
            Divider()
            logContent
        }
        .navigationTitle("日志")
    }

    // ---- 过滤栏 ----
    private var filterBar: some View {
        HStack(spacing: 10) {
            Picker("过滤", selection: $model.logFilter) {
                Text("全部").tag(LogLevel?.none)
                ForEach(LogLevel.allCases, id: \.self) { level in
                    Text(level.label).tag(LogLevel?.some(level))
                }
            }
            .pickerStyle(.menu)
            .frame(width: 120)

            Spacer()

            Text("\(model.logs.count) 条")
                .font(.caption)
                .foregroundStyle(.secondary)

            Button("清空") { model.logs.removeAll() }
            Button("导出…") { exportLogs() }
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
    }

    // ---- 日志内容 ----
    private var logContent: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 4) {
                ForEach(filteredLogs) { entry in
                    HStack(alignment: .top, spacing: 8) {
                        Circle()
                            .fill(levelColor(entry.level))
                            .frame(width: 8, height: 8)
                            .padding(.top, 5)
                        Text(timeString(entry.timestamp))
                            .font(.system(.caption, design: .monospaced))
                            .foregroundStyle(.tertiary)
                        Text(entry.message)
                            .font(.system(.caption))
                            .foregroundStyle(entry.level == .error
                                             ? AnyShapeStyle(.red)
                                             : AnyShapeStyle(.primary))
                            .textSelection(.enabled)
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding(12)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    // ---- 过滤后日志（新→旧展示）----
    private var filteredLogs: [LogEntry] {
        guard let level = model.logFilter else {
            return model.logs.reversed()
        }
        return model.logs.reversed().filter { $0.level == level }
    }

    private func levelColor(_ level: LogLevel) -> Color {
        switch level {
        case .info: return .secondary
        case .warn: return .orange
        case .error: return .red
        }
    }

    private func timeString(_ date: Date) -> String {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f.string(from: date)
    }

    // ---- 导出日志（NSSavePanel → txt）----
    private func exportLogs() {
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.plainText]
        panel.nameFieldStringValue = "avdc-log.txt"
        panel.begin { resp in
            guard resp == .OK, let url = panel.url else { return }
            let text = model.logs.map {
                "\(timeString($0.timestamp)) [\($0.level.rawValue.uppercased())] \($0.message)"
            }.joined(separator: "\n")
            try? text.write(to: url, atomically: true, encoding: .utf8)
        }
    }
}
