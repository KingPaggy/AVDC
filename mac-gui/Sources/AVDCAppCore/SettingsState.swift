import Foundation
import Observation

// 配置字段类型（对齐 QML 8 种 Config 控件）
public enum FieldType {
    case string                  // ConfigInput → TextField
    case toggle                  // ConfigSwitchInt → Toggle
    case choice([(value: String, label: String)])   // ConfigRadioGroup → Picker
    case slider(min: Int, max: Int)                 // ConfigSlider → Slider
    case multiToggle([String])   // ConfigCheckbox 组 → 多个 Toggle
}

public struct SettingsField: Identifiable {
    public let id: String        // section.key（config get/set 用）
    public let label: String
    public let type: FieldType
}

public struct SettingsSection: Identifiable {
    public let id: String
    public let title: String
    public let fields: [SettingsField]
}

// 设置页状态：加载 cli.py config list，变更字段逐个 config set（串行）
@Observable
public final class SettingsState {
    // 字段定义（对照 pyside6_gui/qml/SettingsPage.qml 10 组 + config.ini）
    public static let sections: [SettingsSection] = [
        SettingsSection(id: "common", title: "通用", fields: [
            SettingsField(id: "common.main_mode", label: "模式",
                          type: .choice([("1", "刮削模式"), ("2", "整理模式")])),
            SettingsField(id: "common.soft_link", label: "软链接",
                          type: .choice([("0", "关"), ("1", "开")])),
            SettingsField(id: "common.failed_file_move", label: "失败文件移动",
                          type: .choice([("0", "关"), ("1", "开")])),
            SettingsField(id: "debug_mode.switch", label: "调试模式",
                          type: .toggle),
            SettingsField(id: "update.update_check", label: "检查更新",
                          type: .toggle),
            SettingsField(id: "log.save_log", label: "保存日志", type: .toggle),
            SettingsField(id: "common.success_output_folder",
                          label: "成功输出文件夹", type: .string),
            SettingsField(id: "common.failed_output_folder",
                          label: "失败输出文件夹", type: .string),
        ]),
        SettingsSection(id: "proxy", title: "代理", fields: [
            SettingsField(id: "proxy.type", label: "代理类型",
                          type: .choice([("no", "无"), ("http", "HTTP"),
                                         ("socks5", "SOCKS5")])),
            SettingsField(id: "proxy.proxy", label: "代理地址", type: .string),
            SettingsField(id: "proxy.timeout", label: "超时 (秒)",
                          type: .slider(min: 1, max: 30)),
            SettingsField(id: "proxy.retry", label: "重试次数",
                          type: .slider(min: 0, max: 10)),
        ]),
        SettingsSection(id: "naming", title: "命名规则", fields: [
            SettingsField(id: "Name_Rule.folder_name", label: "文件夹名",
                          type: .string),
            SettingsField(id: "Name_Rule.naming_media", label: "媒体命名",
                          type: .string),
            SettingsField(id: "Name_Rule.naming_file", label: "文件命名",
                          type: .string),
        ]),
        SettingsSection(id: "media", title: "媒体", fields: [
            SettingsField(id: "media.media_type", label: "文件类型",
                          type: .string),
            SettingsField(id: "media.sub_type", label: "字幕类型",
                          type: .string),
            SettingsField(id: "media.media_path", label: "媒体路径",
                          type: .string),
        ]),
        SettingsSection(id: "escape", title: "排除", fields: [
            SettingsField(id: "escape.folders", label: "排除文件夹",
                          type: .string),
            SettingsField(id: "escape.string", label: "排除字符串",
                          type: .string),
            SettingsField(id: "escape.literals", label: "排除文字（正则）",
                          type: .string),
        ]),
        SettingsSection(id: "mark", title: "水印", fields: [
            SettingsField(id: "mark.poster_mark", label: "封面添加水印",
                          type: .toggle),
            SettingsField(id: "mark.thumb_mark", label: "缩略图添加水印",
                          type: .toggle),
            SettingsField(id: "mark.mark_size", label: "水印大小",
                          type: .slider(min: 1, max: 30)),
            SettingsField(id: "mark.mark_type", label: "水印文字",
                          type: .multiToggle(["SUB", "LEAK", "UNCENSORED"])),
            SettingsField(id: "mark.mark_pos", label: "水印位置",
                          type: .choice([("top_left", "左上"),
                                         ("top_right", "右上"),
                                         ("bottom_left", "左下"),
                                         ("bottom_right", "右下")])),
        ]),
        SettingsSection(id: "uncensored", title: "无码", fields: [
            SettingsField(id: "uncensored.uncensored_poster", label: "无码海报",
                          type: .choice([("0", "官方"), ("1", "裁剪")])),
            SettingsField(id: "uncensored.uncensored_prefix", label: "无码前缀",
                          type: .string),
        ]),
        SettingsSection(id: "download", title: "下载", fields: [
            SettingsField(id: "file_download.nfo", label: "下载 NFO",
                          type: .toggle),
            SettingsField(id: "file_download.poster", label: "下载 Poster",
                          type: .toggle),
            SettingsField(id: "file_download.fanart", label: "下载 Fanart",
                          type: .toggle),
            SettingsField(id: "file_download.thumb", label: "下载 Thumb",
                          type: .toggle),
            SettingsField(id: "extrafanart.extrafanart_download",
                          label: "下载 ExtraFanart", type: .toggle),
            SettingsField(id: "extrafanart.extrafanart_folder",
                          label: "ExtraFanart 文件夹", type: .string),
        ]),
        SettingsSection(id: "emby", title: "Emby 客户端", fields: [
            SettingsField(id: "emby.emby_url", label: "Emby 地址",
                          type: .string),
            SettingsField(id: "emby.api_key", label: "API Key",
                          type: .string),
        ]),
        SettingsSection(id: "baidu", title: "百度 AI（人脸检测）", fields: [
            SettingsField(id: "baidu.app_id", label: "App ID", type: .string),
            SettingsField(id: "baidu.api_key", label: "API Key", type: .string),
            SettingsField(id: "baidu.secret_key", label: "Secret Key",
                          type: .string),
        ]),
    ]

    // 所有字段扁平列表
    public static var allFields: [SettingsField] {
        sections.flatMap { $0.fields }
    }

    // key → 当前值（config 值字符串）
    public var values: [String: String] = [:]
    // load 时的快照（save 对比变更字段）
    private var originalValues: [String: String] = [:]
    public var isLoading = false
    public var isSaving = false
    public var message = ""
    // 工具条交互态（CLT 无 @State，局部 UI 状态放模型）
    public var query = ""            // 字段搜索
    public var pendingReset = false   // 恢复默认确认弹窗

    // 按搜索词过滤后的分组（空词 = 全量）
    public var filteredSections: [SettingsSection] {
        let q = query.trimmingCharacters(in: .whitespaces)
        guard !q.isEmpty else { return Self.sections }
        return Self.sections.compactMap { section in
            let fields = section.fields.filter {
                $0.label.localizedCaseInsensitiveContains(q)
                || $0.id.localizedCaseInsensitiveContains(q)
            }
            return fields.isEmpty ? nil
                : SettingsSection(id: section.id,
                                  title: section.title,
                                  fields: fields)
        }
    }

    // 加载：cli.py config list → values
    public func load(using bridge: Bridge) async {
        isLoading = true
        await withCheckedContinuation { cont in
            bridge.configList { lines, _ in
                var d: [String: String] = [:]
                for line in lines ?? [] {
                    let parts = line.split(separator: "=", maxSplits: 1)
                    if parts.count == 2 {
                        let k = parts[0].trimmingCharacters(in: .whitespaces)
                        let v = parts[1].trimmingCharacters(in: .whitespaces)
                        d[k] = v
                    }
                }
                self.values = d
                self.originalValues = d
                self.isLoading = false
                cont.resume()
            }
        }
    }

    // 保存：仅变更字段，串行 config set（避免 config.ini 并发写）
    public func save(using bridge: Bridge) async {
        let changed = Self.allFields.filter {
            values[$0.id] != originalValues[$0.id]
        }
        guard !changed.isEmpty else {
            message = "无变更"
            return
        }
        isSaving = true
        message = "保存中…"
        var failCount = 0
        for field in changed {
            guard let v = values[field.id] else { continue }
            let ok = await setField(bridge, field.id, v)
            if !ok { failCount += 1 }
        }
        originalValues = values
        isSaving = false
        message = failCount == 0
            ? "已保存 \(changed.count) 项"
            : "完成，\(failCount) 项失败"
    }

    // 单个字段保存（串行 await）
    private func setField(_ bridge: Bridge, _ key: String,
                          _ value: String) async -> Bool {
        await withCheckedContinuation { cont in
            bridge.configSet(key, value) { err in
                cont.resume(returning: err == nil)
            }
        }
    }

    // 恢复默认：cli.py config reset 写回默认值，再重新加载
    public func reset(using bridge: Bridge) async {
        isLoading = true
        message = "恢复默认…"
        await withCheckedContinuation { cont in
            bridge.configReset { _ in cont.resume() }
        }
        await load(using: bridge)
        message = "已恢复默认"
    }

    // multiToggle 辅助：值列表是否包含某选项
    public static func multiContains(_ value: String?, _ option: String) -> Bool {
        guard let v = value else { return false }
        return v.split(separator: ",").map(String.init).contains(option)
    }

    // 设置 multiToggle 值（options 顺序拼逗号串）
    public static func multiValue(_ options: [String],
                                  isOn: (String) -> Bool) -> String {
        options.filter(isOn).joined(separator: ",")
    }
}
