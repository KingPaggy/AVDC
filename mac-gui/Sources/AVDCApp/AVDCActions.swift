import AppKit
import AVDCAppCore

// 共享动作：菜单项、工具栏按钮共用同一实现（避免「有按钮无菜单」）

enum AVDCActions {

    /// 选择影片目录（菜单 ⌘O / 主页工具栏共用）
    @MainActor
    static func chooseInputDirectory() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.prompt = "选择"
        let model = AppModel.shared
        if !model.inputDir.isEmpty {
            panel.directoryURL = URL(fileURLWithPath: model.inputDir)
        }
        panel.begin { resp in
            guard resp == .OK, let url = panel.url else { return }
            model.inputDir = url.path
        }
    }

    /// 导出日志（菜单 ⌘E / 日志工具栏共用）
    @MainActor
    static func exportLogs() {
        let logs = AppModel.shared.logs
        guard !logs.isEmpty else { return }
        let panel = NSSavePanel()
        panel.allowedContentTypes = [.plainText]
        panel.nameFieldStringValue = "avdc-log.txt"
        panel.begin { resp in
            guard resp == .OK, let url = panel.url else { return }
            let text = logs.map {
                "\(Self.timeString($0.timestamp)) "
                + "[\($0.level.rawValue.uppercased())] \($0.message)"
            }.joined(separator: "\n")
            try? text.write(to: url, atomically: true, encoding: .utf8)
        }
    }

    static func timeString(_ date: Date) -> String {
        timeFormatter.string(from: date)
    }

    private static let timeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "HH:mm:ss"
        return f
    }()
}
