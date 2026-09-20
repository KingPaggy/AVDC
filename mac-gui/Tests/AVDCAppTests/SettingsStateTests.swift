import Testing
import Foundation
@testable import AVDCAppCore

// SettingsState 测试：config list 加载 / diff 保存（mock CLI，离线）
struct SettingsStateTests {

    private func makeMockRoot() throws -> String {
        let tmp = NSTemporaryDirectory()
            + "avdc_settings_test_\(UUID().uuidString)"
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

    @Test func testLoadParsesConfigList() async throws {
        let bridge = Bridge(projectRoot: try makeMockRoot())
        let settings = SettingsState()
        await settings.load(using: bridge)
        // mock config list 输出 "common.website = mock"
        #expect(settings.values["common.website"] == "mock")
        #expect(!settings.isLoading)
    }

    @Test func testSaveDiffOnly() async throws {
        let bridge = Bridge(projectRoot: try makeMockRoot())
        let settings = SettingsState()
        await settings.load(using: bridge)
        // 变更一个真实字段（mock config set 返回成功）
        settings.values["common.main_mode"] = "2"
        await settings.save(using: bridge)
        #expect(settings.message.hasPrefix("已保存"))
        #expect(!settings.isSaving)
    }

    @Test func testMultiToggleHelpers() {
        let value = "SUB,LEAK"
        #expect(SettingsState.multiContains(value, "SUB"))
        #expect(SettingsState.multiContains(value, "LEAK"))
        #expect(!SettingsState.multiContains(value, "UNCENSORED"))
        let rebuilt = SettingsState.multiValue(["SUB", "LEAK", "UNCENSORED"]) {
            SettingsState.multiContains(value, $0)
        }
        #expect(rebuilt == "SUB,LEAK")
    }
}
