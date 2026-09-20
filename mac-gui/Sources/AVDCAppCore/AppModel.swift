import Foundation
import Observation

// 页面导航枚举（对齐 pyside6_gui 5 个 QML 页面）
public enum Page: Int, CaseIterable, Identifiable {
    case home, settings, tools, log, about

    public var id: Int { rawValue }

    public var title: String {
        switch self {
        case .home: return "主页"
        case .settings: return "设置"
        case .tools: return "工具"
        case .log: return "日志"
        case .about: return "关于"
        }
    }

    public var icon: String {
        switch self {
        case .home: return "house.fill"
        case .settings: return "gearshape.fill"
        case .tools: return "wrench.and.screwdriver.fill"
        case .log: return "doc.text.fill"
        case .about: return "info.circle.fill"
        }
    }
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

    public init(bridge: Bridge = Bridge()) {
        self.bridge = bridge
    }

    public var page: Page = .home

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
    public var logs: [String] = []

    public func appendLog(_ msg: String) {
        guard !msg.isEmpty else { return }
        logs.append(msg)
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

    // 追加结果（cap 200）
    public func addResult(file: String, number: String,
                          status: Int, detail: String) {
        if results.count >= 200 {
            results.removeFirst(results.count - 200)
        }
        results.append(HomeFileResult(file: file, number: number,
                                      status: status, detail: detail))
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
            appendLog(msg)
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
            if !msg.isEmpty { appendLog(msg) }
        }
    }

    // 从文件路径提取番号（文件名去扩展名，完整番号解析在 CLI）
    static func number(from file: String) -> String {
        let url = URL(fileURLWithPath: file)
        return url.deletingPathExtension().lastPathComponent
    }
}
