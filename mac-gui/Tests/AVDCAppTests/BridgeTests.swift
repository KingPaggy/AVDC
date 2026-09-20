import Testing
import Foundation
@testable import AVDCAppCore

// Bridge 冒烟测试：mock 临时项目根 + 假 CLI（离线）
// 覆盖：scan 解析 / config / process 事件流顺序 / terminate 取消
// CLT 无 XCTest，用 Swift Testing（toolchain 自带 Testing.framework）
struct BridgeTests {

    // 构造 mock 项目根：临时目录 + cli/cli.py + pyproject.toml
    private func makeMockRoot() throws -> String {
        let tmp = NSTemporaryDirectory()
            + "avdc_bridge_test_\(UUID().uuidString)"
        let cliDir = tmp + "/cli"
        try FileManager.default.createDirectory(atPath: cliDir,
                                                withIntermediateDirectories: true)

        let src = Bundle.module.url(forResource: "mock_cli",
                                    withExtension: "py")!
        try FileManager.default.copyItem(
            at: src,
            to: URL(fileURLWithPath: cliDir + "/cli.py"))

        let pyproject = """
        [project]
        name = "mock"
        version = "0.0.0"
        requires-python = ">=3.9"
        """
        try pyproject.write(toFile: tmp + "/pyproject.toml",
                            atomically: true, encoding: .utf8)
        return tmp
    }

    @Test func testScan() async throws {
        let root = try makeMockRoot()
        let bridge = Bridge(projectRoot: root)
        let files: [ScanFile] = try await withCheckedThrowingContinuation { cont in
            bridge.scan(path: "/tmp/mock") { files, err in
                if let err { cont.resume(throwing: err) }
                else { cont.resume(returning: files ?? []) }
            }
        }
        #expect(files.count == 1)
        #expect(files.first?.number == "ABC-123")
    }

    @Test func testConfigList() async throws {
        let root = try makeMockRoot()
        let bridge = Bridge(projectRoot: root)
        let lines: [String] = try await withCheckedThrowingContinuation { cont in
            bridge.configList { l, err in
                if let err { cont.resume(throwing: err) }
                else { cont.resume(returning: l ?? []) }
            }
        }
        #expect(lines.count == 1)
        #expect(lines.first?.hasPrefix("common.website") == true)
    }

    @Test func testProcessEvents() async throws {
        let root = try makeMockRoot()
        let bridge = Bridge(projectRoot: root)
        let result: ([String], Int) = try await withCheckedThrowingContinuation { cont in
            var order: [String] = []
            bridge.process(path: "/tmp/mock", mode: 1, onEvent: { event in
                switch event {
                case .log: order.append("log")
                case .progress(let c, _, _):
                    order.append("progress")
                    #expect(c >= 1)
                case .success: order.append("success")
                case .failure(_, let reason):
                    order.append("failure")
                    #expect(!reason.isEmpty)
                case .done(let t, let s, _):
                    order.append("done")
                    #expect(t == 2)
                    #expect(s == 1)
                case .stderr: break
                }
            }, onExit: { status in
                cont.resume(returning: (order, status))
            })
        }
        #expect(result.1 == 0)
        #expect(result.0 == ["log", "progress", "success",
                             "progress", "failure", "done"])
    }

    @Test func testTerminate() async throws {
        let root = try makeMockRoot()
        let bridge = Bridge(projectRoot: root)
        let status = try await withCheckedThrowingContinuation { cont in
            bridge.runCommand(["--path", "/tmp/mock", "--main-mode",
                               "scrape", "--json-output", "--sleep", "5"],
                              onLine: nil, onExit: { st in
                cont.resume(returning: st)
            })
            // 1 秒后取消
            Task {
                try? await Task.sleep(nanoseconds: 1_000_000_000)
                bridge.terminate()
            }
        }
        #expect(status != 0)
    }
}
