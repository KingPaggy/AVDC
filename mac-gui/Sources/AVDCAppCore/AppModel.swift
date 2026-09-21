import Foundation
import Observation

// 页面导航枚举（侧边栏 3 页）
// 设置走 ⌘, 独立 Settings 场景，关于走 App 菜单 About 面板（HIG 标准入口）
public enum Page: Int, CaseIterable, Identifiable {
    case home, tools, log

    public var id: Int { rawValue }

    public var title: String {
        switch self {
        case .home: return "主页"
        case .tools: return "工具"
        case .log: return "日志"
        }
    }

    public var icon: String {
        switch self {
        case .home: return "house.fill"
        case .tools: return "wrench.and.screwdriver.fill"
        case .log: return "doc.text.fill"
        }
    }
}

// 日志级别（Log 页过滤用）
public enum LogLevel: String, CaseIterable {
    case info, warn, error

    public var label: String {
        switch self {
        case .info: return "信息"
        case .warn: return "警告"
        case .error: return "错误"
        }
    }
}

// 日志条目（带级别 + 时间戳）
public struct LogEntry: Identifiable {
    public let id = UUID()
    public let level: LogLevel
    public let message: String
    public let timestamp: Date
}

// 单文件处理结果（Home 结果列表）
public struct HomeFileResult: Identifiable {
    public let id = UUID()
    public var file: String
    public var number: String
    public var status: Int   // 0=待处理 1=成功 2=失败
    public var detail: String
}

// 全局应用状态（@Observable；CLT 无 @State 宏，用单例 + @Bindable）
// Bridge 事件更新，视图层读取驱动刷新
@Observable
public final class AppModel {
    public static let shared = AppModel()

    // Bridge 可注入（测试用 mock 项目根）；默认定位真实 cli/
    public let bridge: Bridge

    // 设置页状态（config.ini 表单）
    public let settings = SettingsState()

    public init(bridge: Bridge = Bridge()) {
        self.bridge = bridge
    }

    public var page: Page = .home

    // 侧边栏显隐（⌘⌥S；CLT 无 @State，放模型由视图绑定）
    public var sidebarHidden = false
    // 搜索聚焦请求计数（⌘F；各页 onChange 自增 → 聚焦本页搜索框）
    public var searchFocusRequest = 0

    // ---- Home 页状态 ----
    public var inputDir = ""
    public var escapeFolders = ""
    public var mode = 1                 // 1=刮削 2=整理
    public var isRunning = false
    public var current = 0
    public var total = 0
    public var success = 0
    public var fail = 0
    public var statusText = ""
    public var results: [HomeFileResult] = []

    // ---- 运行日志（cap 500，供 Log 页）----
    public var logs: [LogEntry] = []
    public var logFilter: LogLevel? = nil   // Log 页过滤级别（nil=全部）
    public var logQuery = ""                // Log 页搜索文本
    public var pendingClearLogs = false     // 清空确认弹窗（CLT 无 @State）
    public var toolMessage: String? = nil   // Tools 页提示（待实现）

    public func appendLog(_ msg: String, level: LogLevel = .info) {
        guard !msg.isEmpty else { return }
        logs.append(LogEntry(level: level, message: msg, timestamp: Date()))
        if logs.count > 500 {
            logs.removeFirst(logs.count - 500)
        }
    }

    // 重置单次处理运行状态
    public func resetProcessing() {
        current = 0
        total = 0
        success = 0
        fail = 0
        results.removeAll()
    }

    // 追加结果（cap 200，新条目置顶，视图无需 reversed）
    public func addResult(file: String, number: String,
                          status: Int, detail: String) {
        if results.count >= 200 {
            results.removeLast(results.count - 199)
        }
        results.insert(HomeFileResult(file: file, number: number,
                                      status: status, detail: detail),
                       at: 0)
    }

    // ---- 批量处理（Bridge 集成）----
    public func startProcessing() {
        guard !isRunning else { return }
        guard !inputDir.isEmpty else {
            statusText = "请先选择输入目录"
            return
        }
        resetProcessing()
        isRunning = true
        statusText = "开始处理…"
        appendLog("开始处理: \(inputDir)"
                  + (mode == 2 ? "（整理模式）" : "（刮削模式）"))

        bridge.process(path: inputDir, mode: mode,
                       onEvent: { [weak self] event in
            self?.handleProcessing(event)
        }, onExit: { [weak self] status in
            guard let self else { return }
            self.isRunning = false
            if status != 0 {
                self.statusText = "处理被中断（已停止）"
                self.appendLog("处理被中断，退出码 \(status)")
            }
        })
    }

    public func stopProcessing() {
        bridge.terminate()
    }

    // Bridge JSONL 事件 → 状态（视图层读取）
    private func handleProcessing(_ event: BridgeEvent) {
        switch event {
        case .log(let msg):
            appendLog(msg, level: .info)
        case .progress(let c, let t, let f):
            current = c
            total = t
            statusText = f
        case .success(let file, let suffix):
            success += 1
            addResult(file: file, number: Self.number(from: file),
                      status: 1, detail: suffix)
        case .failure(let file, let reason):
            fail += 1
            addResult(file: file, number: Self.number(from: file),
                      status: 2, detail: reason)
        case .done(let t, let s, _):
            isRunning = false
            total = t
            success = s
            statusText = "处理完成"
            appendLog("处理完成: 成功 \(s) 失败 \(fail)")
        case .stderr(let msg):
            if !msg.isEmpty { appendLog(msg, level: .error) }
        }
    }

    // 从文件路径提取番号（文件名去扩展名，完整番号解析在 CLI）
    static func number(from file: String) -> String {
        let url = URL(fileURLWithPath: file)
        return url.deletingPathExtension().lastPathComponent
    }
}
