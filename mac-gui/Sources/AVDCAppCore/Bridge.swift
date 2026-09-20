import Foundation

// Bridge 事件（对齐 cli.py --json-output 契约）
//   log / progress / success / failure / done（带 type 字段）
//   stderr：非 JSON 的 stderr 行
public enum BridgeEvent {
    case log(String)
    case progress(current: Int, total: Int, file: String)
    case success(file: String, suffix: String)
    case failure(file: String, reason: String)
    case done(total: Int, success: Int, failed: Int)
    case stderr(String)
}

// scan 结果条目（cli.py scan 输出）
public struct ScanFile: Codable {
    var file: String
    var name: String
    var number: String
    var dir: String
}

// 管道逐行读取器：后台队列累积 Data，按 \n 分割，主线程分发
// （Swift 版 NSTask readabilityHandler + 行缓冲，竞态处理同 ObjC++ 版）
final class PipeReader {
    private var buffer = Data()
    private let queue = DispatchQueue(label: "avdc.bridge.pipe")
    private let onLine: (String) -> Void

    init(onLine: @escaping (String) -> Void) {
        self.onLine = onLine
    }

    func start(_ fh: FileHandle) {
        fh.readabilityHandler = { [weak self] handle in
            guard let self else { return }
            let chunk = handle.availableData
            self.queue.sync {
                if chunk.isEmpty {
                    // EOF：flush 残留（无换行结尾的最后一行）
                    handle.readabilityHandler = nil
                    self.flushLocked()
                    return
                }
                self.buffer.append(chunk)
                while let nl = self.buffer.firstIndex(of: 0x0A) {
                    let lineData = self.buffer.subdata(in: 0..<nl)
                    self.buffer.removeSubrange(0..<(nl + 1))
                    if let s = String(data: lineData, encoding: .utf8),
                       !s.isEmpty {
                        let line = s
                        DispatchQueue.main.async { self.onLine(line) }
                    }
                }
            }
        }
    }

    func flush() {
        queue.sync { flushLocked() }
    }

    private func flushLocked() {
        if !buffer.isEmpty,
           let s = String(data: buffer, encoding: .utf8), !s.isEmpty {
            buffer.removeAll()
            let line = s
            DispatchQueue.main.async { self.onLine(line) }
        }
    }
}

// Python Bridge：Swift Process 调用 `uv run python cli.py <cmd>`
// 契约对齐 cli/cli.py --json-output（docs/03-macos-gui-migration.md §4.3）
public final class Bridge {
    private let projectRoot: String?
    private var task: Process?

    public var isRunning: Bool { task != nil }

    public init(projectRoot: String? = nil) {
        if let root = projectRoot {
            self.projectRoot = root
        } else {
            self.projectRoot = Self.findProjectRoot()
        }
    }

    // 项目根定位：从当前工作目录向上查找含 cli/cli.py 的目录
    public static func findProjectRoot() -> String? {
        var dir = FileManager.default.currentDirectoryPath
        for _ in 0..<10 {
            let cli = (dir as NSString).appendingPathComponent("cli/cli.py")
            if FileManager.default.fileExists(atPath: cli) { return dir }
            let parent = (dir as NSString).deletingLastPathComponent
            if parent == dir { break }
            dir = parent
        }
        return nil
    }

    // 底层：uv run python cli.py <args>；onLine 每行（主线程）、onExit 退出码
    public func runCommand(_ args: [String],
                    onLine: ((String) -> Void)?,
                    onStderr: ((String) -> Void)? = nil,
                    onExit: @escaping (Int) -> Void) {
        guard task == nil else { onExit(-1); return }
        guard let root = projectRoot else {
            onLine?("[bridge] 未找到项目根目录（cli/cli.py）")
            onExit(-1)
            return
        }
        let cliPath = (root as NSString).appendingPathComponent("cli/cli.py")
        let fullArgs = ["uv", "run", "python", cliPath] + args

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/env")
        proc.arguments = fullArgs
        proc.currentDirectoryURL = URL(fileURLWithPath: root)

        let outPipe = Pipe()
        let errPipe = Pipe()
        proc.standardOutput = outPipe
        proc.standardError = errPipe

        let outReader = PipeReader(onLine: { onLine?($0) })
        let errReader = PipeReader(onLine: { (onStderr ?? onLine)?($0) })
        outReader.start(outPipe.fileHandleForReading)
        errReader.start(errPipe.fileHandleForReading)

        proc.terminationHandler = { [weak self] p in
            // 清空 EOF 后残留缓冲
            outReader.flush()
            errReader.flush()
            DispatchQueue.main.async {
                self?.task = nil
                onExit(Int(p.terminationStatus))
            }
        }

        do {
            try proc.run()
            task = proc
        } catch {
            onLine?("[bridge] 启动失败: \(error.localizedDescription)")
            onExit(-1)
        }
    }

    // 取消当前任务（SIGTERM）
    public func terminate() {
        task?.terminate()
    }

    // ---- 命令封装 ----

    // 扫描目录提取番号：cli.py scan --path
    public func scan(path: String, escapeFolder: String? = nil,
              completion: @escaping ([ScanFile]?, Error?) -> Void) {
        var args = ["scan", "--path", path]
        if let ef = escapeFolder, !ef.isEmpty {
            args += ["--escape-folder", ef]
        }
        var files: [ScanFile] = []
        var gotResult = false
        runCommand(args, onLine: { line in
            guard let dict = Self.parseJSON(line),
                  let arr = dict["files"] as? [[String: Any]] else { return }
            gotResult = true
            for f in arr {
                files.append(ScanFile(
                    file: f["file"] as? String ?? "",
                    name: f["name"] as? String ?? "",
                    number: f["number"] as? String ?? "",
                    dir: f["dir"] as? String ?? ""))
            }
        }, onExit: { status in
            if status == 0 && gotResult {
                completion(files, nil)
            } else {
                completion(nil, BridgeError.exit(status, "scan 失败"))
            }
        })
    }

    // 批量处理（刮削/整理）：cli.py --path --main-mode --json-output
    public func process(path: String, mode: Int,
                 onEvent: @escaping (BridgeEvent) -> Void,
                 onExit: @escaping (Int) -> Void) {
        let mainMode = mode == 2 ? "organize" : "scrape"
        let args = ["--path", path, "--main-mode", mainMode, "--json-output"]
        runCommand(args, onLine: { line in
            guard let dict = Self.parseJSON(line) else {
                onEvent(.stderr(line))
                return
            }
            let type = dict["type"] as? String
            switch type {
            case "log":
                if let m = dict["msg"] as? String { onEvent(.log(m)) }
            case "progress":
                if let c = dict["current"] as? Int,
                   let t = dict["total"] as? Int {
                    onEvent(.progress(current: c, total: t,
                                      file: dict["file"] as? String ?? ""))
                }
            case "success":
                onEvent(.success(file: dict["file"] as? String ?? "",
                                 suffix: dict["suffix"] as? String ?? ""))
            case "failure":
                onEvent(.failure(file: dict["file"] as? String ?? "",
                                 reason: dict["reason"] as? String ?? ""))
            case "done":
                onEvent(.done(total: dict["total"] as? Int ?? 0,
                              success: dict["success"] as? Int ?? 0,
                              failed: dict["failed"] as? Int ?? 0))
            default:
                onEvent(.stderr(line))
            }
        }, onExit: onExit)
    }

    // 配置：cli.py config list（section.key = value 行）
    public func configList(completion: @escaping ([String]?, Error?) -> Void) {
        var lines: [String] = []
        runCommand(["config", "list"], onLine: { line in
            if !line.isEmpty { lines.append(line) }
        }, onStderr: { _ in }, onExit: { status in
            if status == 0 {
                completion(lines, nil)
            } else {
                completion(nil, BridgeError.exit(status, "config list 失败"))
            }
        })
    }

    // 配置：cli.py config get <field>
    public func configGet(_ field: String,
                   completion: @escaping (String?, Error?) -> Void) {
        var lines: [String] = []
        runCommand(["config", "get", field], onLine: { line in
            if !line.isEmpty { lines.append(line) }
        }, onStderr: { _ in }, onExit: { status in
            if status == 0 && !lines.isEmpty {
                completion(lines.first, nil)
            } else {
                completion(nil, BridgeError.exit(status, "config get 失败"))
            }
        })
    }

    // 配置：cli.py config set <field> <value>
    public func configSet(_ field: String, _ value: String,
                   completion: @escaping (Error?) -> Void) {
        runCommand(["config", "set", field, value], onLine: nil,
                   onExit: { status in
            completion(status == 0 ? nil
                       : BridgeError.exit(status, "config set 失败"))
        })
    }

    // 配置：cli.py config reset（写回默认值）
    public func configReset(completion: @escaping (Error?) -> Void) {
        runCommand(["config", "reset"], onLine: nil,
                   onExit: { status in
            completion(status == 0 ? nil
                       : BridgeError.exit(status, "config reset 失败"))
        })
    }

    // JSONL 行解析
    public static func parseJSON(_ line: String) -> [String: Any]? {
        guard let data = line.data(using: .utf8) else { return nil }
        return (try? JSONSerialization.jsonObject(with: data))
            as? [String: Any]
    }
}

// Bridge 错误
public enum BridgeError: Error, LocalizedError {
    case exit(Int, String)

    public var errorDescription: String? {
        switch self {
        case .exit(let code, let ctx):
            return "\(ctx)（退出码 \(code)）"
        }
    }
}
