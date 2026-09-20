import SwiftUI
import AVDCAppCore

// 设置页：10 组配置表单（对齐 QML SettingsPage）
// 控件映射：string→TextField、toggle→Toggle、choice→Picker、
// slider→Slider、multiToggle→多 Toggle
struct SettingsView: View {
    @Bindable var settings: SettingsState
    let bridge: Bridge

    var body: some View {
        List {
            ForEach(SettingsState.sections) { section in
                Section(section.title) {
                    ForEach(section.fields) { field in
                        fieldRow(field)
                    }
                }
            }

            // ---- 操作按钮 ----
            Section {
                HStack(spacing: 12) {
                    if settings.isSaving {
                        ProgressView().controlSize(.small)
                    }
                    Text(settings.message)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Button("恢复默认") {
                        Task { await settings.reset(using: bridge) }
                    }
                    Button("保存配置") {
                        Task { await settings.save(using: bridge) }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(settings.isLoading || settings.isSaving)
                }
            }
        }
        .listStyle(.inset)
        .navigationTitle("设置")
        .task {
            if settings.values.isEmpty {
                await settings.load(using: bridge)
            }
        }
        .overlay {
            if settings.isLoading {
                ProgressView("加载配置…")
            }
        }
    }

    // ---- 字段渲染 ----
    @ViewBuilder
    private func fieldRow(_ field: SettingsField) -> some View {
        switch field.type {
        case .string:
            LabeledContent(field.label) {
                TextField("", text: stringBinding(field.id))
                    .textFieldStyle(.roundedBorder)
            }
        case .toggle:
            Toggle(field.label, isOn: boolBinding(field.id))
        case .choice(let options):
            Picker(field.label, selection: stringBinding(field.id)) {
                ForEach(options, id: \.value) { opt in
                    Text(opt.label).tag(opt.value)
                }
            }
        case .slider(let min, let max):
            SliderRow(label: field.label,
                      value: sliderBinding(field.id, min: min, max: max),
                      min: min, max: max)
        case .multiToggle(let options):
            MultiToggleRow(label: field.label, key: field.id,
                           options: options, settings: settings)
        }
    }

    // ---- 字典绑定辅助 ----
    private func stringBinding(_ key: String) -> Binding<String> {
        Binding(get: { settings.values[key] ?? "" },
                set: { settings.values[key] = $0 })
    }

    private func boolBinding(_ key: String) -> Binding<Bool> {
        Binding(get: { settings.values[key] == "1" },
                set: { settings.values[key] = $0 ? "1" : "0" })
    }

    private func sliderBinding(_ key: String, min: Int,
                               max: Int) -> Binding<Double> {
        Binding(get: { Double(settings.values[key] ?? "") ?? Double(min) },
                set: { settings.values[key] = String(Int($0)) })
    }
}

// Slider + 当前值
struct SliderRow: View {
    let label: String
    @Binding var value: Double
    let min: Int
    let max: Int

    var body: some View {
        LabeledContent(label) {
            HStack(spacing: 8) {
                Slider(value: $value, in: Double(min)...Double(max), step: 1)
                Text("\(Int(value))")
                    .monospacedDigit()
                    .frame(width: 32, alignment: .trailing)
            }
        }
    }
}

// 多选 Toggle 组（如水印文字 SUB/LEAK/UNCENSORED）
struct MultiToggleRow: View {
    let label: String
    let key: String
    let options: [String]
    @Bindable var settings: SettingsState

    var body: some View {
        LabeledContent(label) {
            HStack {
                ForEach(options, id: \.self) { opt in
                    Toggle(opt, isOn: toggleBinding(opt))
                }
            }
        }
    }

    private func toggleBinding(_ opt: String) -> Binding<Bool> {
        Binding(
            get: { SettingsState.multiContains(settings.values[key], opt) },
            set: { on in
                var parts = (settings.values[key] ?? "")
                    .split(separator: ",").map(String.init)
                if on {
                    if !parts.contains(opt) { parts.append(opt) }
                } else {
                    parts.removeAll { $0 == opt }
                }
                settings.values[key] = parts.joined(separator: ",")
            })
    }
}
