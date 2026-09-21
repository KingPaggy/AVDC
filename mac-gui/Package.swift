// swift-tools-version:6.2
// AVDC macOS GUI — 纯 SwiftUI + Swift Process Bridge
// 构建：swift build  /  运行：.build/debug/AVDC  /  测试：swift test
// 部署目标 macOS 26（Liquid Glass / ToolbarSpacer 等新设计 API 直用，
// 不再用 #available 分支）；无 bundle，进程名即 App 菜单名 → 产物叫 AVDC
import PackageDescription

let package = Package(
    name: "AVDCMacGUI",
    platforms: [.macOS(.v26)],   // 决策 3：min macOS 26
    products: [
        .executable(name: "AVDC", targets: ["AVDCApp"]),
    ],
    targets: [
        // 逻辑层（Foundation only，可单测）：Bridge + AppModel
        .target(name: "AVDCAppCore"),
        // 可执行层：SwiftUI 视图（依赖 Core）
        .executableTarget(
            name: "AVDCApp",
            dependencies: ["AVDCAppCore"],
            linkerSettings: [
                .linkedFramework("SwiftUI"),
                .linkedFramework("AppKit"),
            ]
        ),
        // 测试：Bridge 冒烟测试（mock CLI，离线）
        // CLT 无 XCTest，用 Swift Testing（toolchain 自带）
        .testTarget(
            name: "AVDCAppTests",
            dependencies: ["AVDCAppCore"],
            resources: [.copy("Resources/mock_cli.py")],
            swiftSettings: [
                .unsafeFlags(["-F",
                    "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"]),
                // CLT 下 SPM 偶发不传 Testing 宏插件路径，手动补齐
                .unsafeFlags(["-plugin-path",
                    "/Library/Developer/CommandLineTools/usr/lib/swift/host/plugins/testing"])
            ],
            linkerSettings: [
                .unsafeFlags(["-F",
                    "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"])
            ]
        ),
    ],
    // CLT 无 SwiftUIMacros：保持 Swift 5 语义，避免 Swift 6 严格并发
    // 对 AppModel.shared / SettingsState.sections 等全局态报错
    swiftLanguageModes: [.v5]
)
