import Testing
import Foundation
@testable import AVDCAppCore

// AppModel 链路测试：startProcessing → Bridge(mock) → 状态更新
// Bridge 事件派发主线程，测试用 RunLoop.main 轮询 drain
struct AppModelTests {

    // 构造 mock 项目根（同 BridgeTests）
    private func makeMockRoot() throws -> String {
        let tmp = NSTemporaryDirectory()
            + "avdc_model_test_\(UUID().uuidString)"
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

    @Test func testProcessingUpdatesState() async throws {
        let root = try makeMockRoot()
        let model = AppModel(bridge: Bridge(projectRoot: root))
        model.inputDir = "/tmp/mock"
        model.mode = 1
        model.startProcessing()

        // 等待完成（mock 事件流约 0.1s；drain 主线程事件）
        let deadline = Date().addingTimeInterval(15)
        while model.isRunning && Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.05))
            try await Task.sleep(nanoseconds: 10_000_000)
        }

        #expect(!model.isRunning)
        #expect(model.total == 2)
        #expect(model.success == 1)
        #expect(model.fail == 1)
        #expect(model.results.count == 2)
        #expect(model.results.first?.status == 1)   // 存储序：先 success
        #expect(model.results.last?.status == 2)    // 后 failure
        #expect(model.logs.count >= 3)              // 开始 + mock log + 完成
    }
}
