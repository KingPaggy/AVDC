import SwiftUI
import AVDCAppCore

// 关于页：版本 / 技术栈 / 项目信息（对齐 QML AboutPage）
struct AboutView: View {
    var body: some View {
        VStack(spacing: 14) {
            Text("AVDC")
                .font(.system(size: 34, weight: .bold))
            Text("macOS 原生版 · SwiftUI")
                .font(.body)
                .foregroundStyle(.tertiary)

            Divider().frame(width: 260)

            VStack(spacing: 6) {
                infoRow("版本", "0.2.0")
                infoRow("核心", "Python 3.13 · avdc-core")
                infoRow("界面", "SwiftUI · Observation · Process Bridge")
                infoRow("设计", "Apple HIG 设计规范")
            }
            .font(.body)

            Divider().frame(width: 260)

            Text("AVDC（AV Data Capture）— 自动抓取元数据并整理\n本地视频文件，输出供 Emby / Kodi / Plex 使用")
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .lineSpacing(4)
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .navigationTitle("关于")
    }

    private func infoRow(_ label: String, _ value: String) -> some View {
        HStack(spacing: 10) {
            Text(label)
                .foregroundStyle(.secondary)
                .frame(width: 44, alignment: .trailing)
            Text(value)
        }
    }
}
