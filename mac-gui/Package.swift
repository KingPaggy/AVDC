// swift-tools-version:5.9
// AVDC macOS GUI — 纯 SwiftUI + Swift Process Bridge
// 构建：swift build  /  测试：swift test
import PackageDescription

let package = Package(
    name: "AVDCMacGUI",
    platforms: [.macOS(.v14)],   // min 部署；glassEffect 用 #available 防护
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
                    "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"])
            ],
            linkerSettings: [
                .unsafeFlags(["-F",
                    "/Library/Developer/CommandLineTools/Library/Developer/Frameworks"])
            ]
        ),
    ]
)
