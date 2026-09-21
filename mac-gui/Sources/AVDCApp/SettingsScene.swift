import SwiftUI
import AVDCAppCore

// 设置窗口（⌘,）：HIG 偏好窗口形态 —— grouped 表单 + 工具栏保存/恢复默认
// 保存与恢复默认只在工具栏出现，内容区只放字段（导航层/内容层分离）
struct SettingsScene: View {
    @Bindable var state: SettingsState
    let bridge: Bridge
    @FocusState private var searchFocused: Bool   // ⌘F 聚焦搜索框

    var body: some View {
        Form {
            ForEach(state.filteredSections) { section in
                Section(section.title) {
                    ForEach(section.fields) { field in
                        SettingsRow(field: field, state: state)
                    }
                }
            }
            Section {
                HStack(spacing: Metric.item) {
                    if state.isSaving {
                        ProgressView().controlSize(.small)
                    }
                    Text(state.message)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Spacer()
                }
            }
        }
        .formStyle(.grouped)
        .frame(minWidth: 460, minHeight: 420)
        .searchable(text: $state.query, placement: .toolbar,
                    prompt: "搜索设置项")
        .searchFocused($searchFocused)
        .onChange(of: state.searchFocusRequest) { searchFocused = true }
        .toolbar { toolbarContent }
        .task {
            if state.values.isEmpty { await state.load(using: bridge) }
        }
        .overlay {
            if state.isLoading { ProgressView("加载配置…") }
        }
        .confirmationDialog("恢复默认配置？", isPresented: $state.pendingReset) {
            Button("恢复默认", role: .destructive) {
                Task { await state.reset(using: bridge) }
            }
            Button("取消", role: .cancel) {}
        } message: {
            Text("将把 config.ini 的可配置项全部写回默认值，不可撤销。")
        }
    }

    @ToolbarContentBuilder
    private var toolbarContent: some ToolbarContent {
        ToolbarItem(placement: .primaryAction) {
            Button("保存配置") {
                Task { await state.save(using: bridge) }
            }
            .keyboardShortcut("s", modifiers: .command)
            .disabled(state.isLoading || state.isSaving)
            .help("保存变更到 config.ini")
        }
        ToolbarItem(placement: .primaryAction) {
            Button("恢复默认") { state.pendingReset = true }
                .disabled(state.isLoading || state.isSaving)
                .help("把配置写回默认值")
        }
    }
}

// ---- 字段渲染 ----
// 控件映射：string→TextField、toggle→Toggle、choice→Picker、
// slider→Slider、multiToggle→多 Toggle
struct SettingsRow: View {
    let field: SettingsField
    @Bindable var state: SettingsState

    var body: some View {
        switch field.type {
        case .string:
            LabeledContent(field.label) {
                TextField("", text: stringBinding)
                    .textFieldStyle(.roundedBorder)
                    .frame(minWidth: 200)
            }
        case .toggle:
            Toggle(field.label, isOn: boolBinding)
        case .choice(let options):
            Picker(field.label, selection: stringBinding) {
                ForEach(options, id: \.value) { opt in
                    Text(opt.label).tag(opt.value)
                }
            }
        case .slider(let min, let max):
            LabeledContent(field.label) {
                HStack(spacing: Metric.item) {
                    Slider(value: sliderBinding(min, max),
                           in: Double(min)...Double(max), step: 1)
                    Text("\(Int(sliderBinding(min, max).wrappedValue))")
                        .monospacedDigit()
                        .frame(width: 32, alignment: .trailing)
                }
            }
        case .multiToggle(let options):
            LabeledContent(field.label) {
                HStack(spacing: Metric.item) {
                    ForEach(options, id: \.self) { opt in
                        Toggle(opt, isOn: multiBinding(opt))
                    }
                }
            }
        }
    }

    // ---- 字典绑定辅助 ----
    private var stringBinding: Binding<String> {
        Binding(get: { state.values[field.id] ?? "" },
                set: { state.values[field.id] = $0 })
    }

    private var boolBinding: Binding<Bool> {
        Binding(get: { state.values[field.id] == "1" },
                set: { state.values[field.id] = $0 ? "1" : "0" })
    }

    private func sliderBinding(_ min: Int, _ max: Int) -> Binding<Double> {
        Binding(
            get: { Double(state.values[field.id] ?? "") ?? Double(min) },
            set: { state.values[field.id] = String(Int($0)) })
    }

    private func multiBinding(_ opt: String) -> Binding<Bool> {
        Binding(
            get: { SettingsState.multiContains(state.values[field.id], opt) },
            set: { on in
                var parts = (state.values[field.id] ?? "")
                    .split(separator: ",").map(String.init)
                if on {
                    if !parts.contains(opt) { parts.append(opt) }
                } else {
                    parts.removeAll { $0 == opt }
                }
                state.values[field.id] = parts.joined(separator: ",")
            })
    }
}
