# AVDC macOS GUI 迁移方案（纯 SwiftUI 版）

> 目标：为 AVDC 构建 macOS 原生 GUI，替换 PySide6 主力前端。
> 技术选型：**纯 SwiftUI + Swift Process Bridge**（废弃 ImGui/
> Metal/ObjC++ 薄壳路线）。
> 状态：✅ 已执行完成（2026-09-20，5 页全部落地，测试 8/8
> 通过；PySide6/PyQt5 已归档 .archive/）
> updated: 2026-09-20
>
> ⚠️ 2026-09-21 结构已重排（侧边栏 3 页 + ⌘, 设置窗口 +
> 系统 About 面板 + 工具栏/菜单/设计令牌，min macOS 26、
> 不打包 .app）：本文档描述的 5 页视图结构为历史记录，
> 现行方案见
> [report-2026-09-21-1016-macGUI-官方设计标准对齐优化方案.md](report-2026-09-21-1016-macGUI-官方设计标准对齐优化方案.md)。

## 1. 调研结论

### 1.1 AVDC 现状

- Python 3.13 + uv workspace，四包：`core/`、`cli/`、
  `pyqt5-gui/`（遗留）、`pyside6_gui/`（主力）
- `core/`：64 个 .py，约 3450 行——7 站点爬虫、CoreEngine
  编排、AppConfig、EventBus、图片水印，零 Qt 依赖
- `pyside6_gui/`：5 个 QML 页面 + 15 组件 + 3 个 Python 模型
- `cli/`：CLI 前端，已支持 `--json-output` + 流式 JSONL
- `tui-go/`：Go TUI（保留），已验证「子进程 + JSON」模式

### 1.2 关键约束

1. **核心不重构**：业务核心是 Python（爬虫/lxml/Pillow），
   已决策以 JSONL 契约隔离保未来（见 §4）
2. **桥接基础现成**：CLI 已支持 `--json-output` 流式输出，
   事件契约：log/progress/success/failure/done + scan
   `{files,total}`
3. **GUI 形态是标准数据管理界面**（表单/列表/进度/文本/
   卡片），无任何自绘图形需求——这是弃 ImGui 的根因
4. **CLT 环境约束**：无 Xcode.app，`@State` 宏不可用
   （缺 SwiftUIMacros 插件），但 `@Observable` + `@Bindable`
   宏可用（Observation 框架，已实测验证）
5. **Swift Process 可用**：Swift 原生 `Process` +
   `readabilityHandler` 流式读 JSONL（已实测），替代
   ObjC++ NSTask

## 2. 技术选型决策（2026-09-20）

### 2.1 为什么弃 ImGui/Metal 路线

原计划复用 14-MacApp-C-Cpp 四层架构（C++ core + ObjC++
薄壳 + ImGui/Metal 自绘 + SwiftUI 原生玻璃）。但 AVDC 与
14-MacApp 本质不同：

| 维度 | 14-MacApp（波形工具） | AVDC（数据管理） |
|------|----------------------|------------------|
| 内容 | 高频自绘波形/坐标轴 | 表单/列表/进度/文本 |
| ImGui 价值 | 高（自绘曲线） | 低（无自绘需求） |
| 原生控件可覆盖 | 否 | **完全覆盖** |

ImGui 路线对 AVDC 是过度设计，且引入大量纯负担：

- 中文渲染（PingFang font atlas 手工维护）
- 表单控件自绘（checkbox/input/slider/radio 全手写）
- 语义色每帧注入、浅深色手动适配
- 无障碍（减透明度/动效/高对比）手动处理
- ImGui 控件事件 → ObjC++ 回调桥接
- 第三方源码依赖（third_party/imgui）

SwiftUI 全部免费获得：原生控件、无障碍、浅深色、
国际化、焦点/键盘导航、Liquid Glass（macOS 26 原生）。

### 2.2 可行性验证（CLT 实测）

| 项 | 结果 |
|----|------|
| `@State` 宏 | ❌ 缺 SwiftUIMacros 插件（已知坑） |
| `@Observable`/`@Bindable` | ✅ 可用（Observation 宏） |
| `@Published`/`@ObservedObject` | ✅ 可用 |
| Swift `Process` 异步 JSONL | ✅ 可用 |
| SPM `swift build`（SwiftUI executable） | ✅ 26s 构建通过 |
| NavigationSplitView | ✅ 编译通过 |

### 2.3 新目标架构

```
mac-gui/
├── Package.swift              # SPM（替代 CMake）
├── Sources/AVDCApp/
│   ├── AVDCApp.swift          # @main App + WindowGroup
│   ├── AppModel.swift         # @Observable 全局状态
│   ├── Bridge.swift           # Process 封装（JSONL 事件）
│   ├── Sidebar.swift          # NavigationSplitView 5 页
│   ├── HomeView.swift         # 主页（表单/进度/结果）
│   ├── SettingsView.swift     # 设置页（8 组配置表单）
│   ├── ToolsView.swift        # 工具页（卡片网格）
│   ├── LogView.swift          # 日志页（级别过滤）
│   └── AboutView.swift        # 关于页
└── Tests/AVDCAppTests/        # Bridge 测试（复用 mock_cli.py）
```

- 状态：`AppModel`（@Observable）承载 page/home/logs，
  替代 C++ `AppState`
- Bridge：Swift `Process` 调 `uv run python cli.py`，
  移植已验证的 AVDCBridge 逻辑
- 构建：`swift build` / `swift test`，无 CMake/ImGui

### 2.4 待废弃（ImGui 路线投入）

| 目录/文件 | 处理 |
|-----------|------|
| `third_party/imgui/` | 删除（git 历史保留记录） |
| `src/ui/`（UIManager/Palette/UIConfig） | 删除 |
| `src/core/`（C++ AppState） | 删除（Swift AppModel 替代） |
| `src/bridge/`（ObjC++ AVDCBridge） | 重写为 Swift Bridge.swift |
| `src/shell/AppDelegate.*`、`Menus.*`、`main.mm` | 删除 |
| `CMakeLists.txt`（4 个） | 删除（Package.swift 替代） |
| `src/shell/Sidebar.swift`、`InfoBar.swift` | 参考思路，被原生
  NavigationSplitView / glassEffect 替代 |

> 已投入的阶段 0（骨架）、1（Bridge 冒烟测试）、2（Home
> ImGui）的提交保留在 git 历史；阶段 2 未提交的工作区改动
> 将随重构废弃。ImGui 的「语义色 + 无障碍」思路已沉淀到
> 14-MacApp 项目，不丢失。

## 3. 执行步骤（纯 SwiftUI 版）

> 已完成的 ImGui 路线阶段 0/1/2 不继续，重新按以下步骤。
> 每阶段完成后 git 提交。

### 阶段 0′：SPM 骨架 + 状态模型 + Swift Bridge（1–2 人日）

- 建 `Package.swift`（.macOS(.v14)，SwiftUI+AppKit 框架）
- `AppModel.swift`：@Observable 全局状态（page 枚举、
  HomeState 等价物、logs 数组）
- `Bridge.swift`：Process 封装 + JSONL 逐行解析 + 事件回调
  （移植 AVDCBridge.mm：进度/成功/失败/完成/日志 + 取消）
- `Sidebar.swift`：NavigationSplitView 5 页导航
  （主页/设置/工具/日志/关于，SF Symbols 图标）
- `InfoBar.swift` 思路并入：工具栏/标题 + 全屏 `.glassEffect`
- Bridge 测试：Swift Testing/XCTest + mock_cli.py（复用
  阶段 1 的 mock，断言事件顺序与取消）
- 产出：可运行空壳 + 5 页导航 + Bridge 测试通过

### 阶段 1′：Home 页（0.5–1 人日）

- 输入区：TextField 目录 + 排除文件夹 + 目录选择
  （`.fileImporter`/NSOpenPanel）
- 模式单选（刮削/整理 Picker）+ 开始/停止按钮
- `ProgressView` 进度 + 成功/失败/总数徽章
- 结果列表（List：状态色 + 番号 + 文件 + 详情）
- 端到端验证：fixtures organize 链路（复用 smoke 思路）

### 阶段 2′：Settings 页（1–1.5 人日）

- 8 组配置表单（通用/代理/命名规则/媒体/排除/水印/Emby/
  其他，对照 SettingsPage.qml 347 行）
- SwiftUI 原生控件：Toggle/TextField/Slider/Picker/
  FileImporter 对应 QML 8 种控件
- 读写走 `cli.py config get/set`，保存按钮统一提交

### 阶段 3′：Tools / Log / About 页（0.5–1 人日）

- Tools：卡片网格（LazyVGrid + 工具卡片，部分「待实现」
  按现状迁移）
- Log：日志查看（ScrollView + 级别过滤），数据来自
  AppModel.logs（Home 过程实时追加）
- About：版本信息 + 项目链接

### 阶段 4′：打磨 + 清理（0.5–1 人日）

- 浅/深色、无障碍、全屏（SwiftUI 原生，验证即可）
- 删除 ImGui/ObjC++ 残留（§2.4 清单）
- 更新 README、docs/、AGENTS.md；清理 pyproject workspace
  成员（pyside6/pyqt5 归档）

## 4. core/cli 重构评估（决策记录）

> 已决策（2026-09-20）：**不重构 core/cli**，以 JSONL
> 契约隔离保未来。

### 4.1 负载类型判断

AVDC 工作负载以 I/O 绑定为主（网络等待 + 站点限速），
非 CPU 绑定；高性能语言优势不明显。

| 模块 | 负载类型 | 换 Go/Rust 收益 | 结论 |
|------|---------|----------------|------|
| 网络抓取 | I/O 绑定 | 瓶颈在远端限速/封禁；
  反爬生态弱 | 不重构 |
| HTML 解析 | CPU 轻 | lxml 已 C 绑定，差距小 | 类似 |
| 文件扫描 | I/O 绑定 | 3–10x 但绝对耗时秒级 | 可选定点 |
| 图片水印 | CPU 中 | Pillow 已 C 加速 | 类似 |
| 批量编排 | 混合 | 瓶颈仍是网络 | 不重构 |

### 4.2 不重构理由

- 重写成本：64 文件 / 3450 行 + 7 爬虫 + 3 套测试
- 反爬是最大隐性成本（Cloudflare 对抗，Python 生态最成熟）

### 4.3 契约隔离保障

- Bridge 只认 `cli.py --json-output` 的 JSONL 契约
- 未来若 scan 实测变慢，单独 Go 重写（纯文件系统，
  约 1–2 天），其余保持 Python
- 触发条件：Python 自身耗时占比 > 20% 才评估

## 5. 剩余文件清理

| 文件/目录 | 处理 | 理由 |
|----------|------|------|
| `pyside6_gui/` | 迁移完成即移入 `.archive/` | 无并行维护期 |
| `pyqt5-gui/` | 移入 `.archive/` | 遗留前端 |
| `tui-go/` | 保留 | 终端场景独立价值 |
| `cli/` + `core/` | 保留 | 事实来源，Bridge 依赖 |
| `mac-gui/` 旧残留 | 删除（§2.4） | ImGui/ObjC++ 废弃 |
| `pyproject.toml` | 移除已归档 workspace 成员 | 避免 uv sync 失败 |
| `README.md`/`docs/`/`AGENTS.md` | 同步更新 | 前端说明与记忆 |

> 归档时机：mac-gui 迁移完成并验证后执行。

## 6. 工作量汇总（纯 SwiftUI 版）

| 阶段 | 内容 | 工作量（人日） |
|------|------|---------------|
| 0′ | SPM 骨架 + AppModel + Bridge | 1–2 |
| 1′ | Home 页 | 0.5–1 |
| 2′ | Settings 页 | 1–1.5 |
| 3′ | Tools/Log/About | 0.5–1 |
| 4′ | 打磨 + 清理 | 0.5–1 |
| **合计** | | **约 4–6 人日** |

对比 ImGui 路线（9.5–15 人日）**约节省 60%**，且体验更好
（原生控件 + 无障碍 + 深浅色免费获得）。

## 7. 风险与未决事项

| 风险 | 等级 | 缓解 |
|------|------|------|
| CLT 宏限制（@State 不可用） | 低 | 用 @Observable/@Bindable，
  已实测验证 |
| SPM 构建 app bundle 缺失 | 低 | 裸可执行可运行（14-MacApp
  已验证）；如需图标后续加 bundle |
| Process 取消语义 | 低 | 阶段 1 ObjC++ 已验证
  SIGTERM 路径 |
| Settings 表单量大 | 低 | 8 种控件均原生，工作量小 |
| SwiftUI 无标题栏观感差异 | 低 | AVDC 用原生 WindowGroup，
  不复刻 14-MacApp 花活 |

未决事项：
- 目录命名 `mac-gui/` 已定；是否保留 build 产物
  （`.build/` 进 .gitignore）
- Swift 测试框架选 XCTest 还是 Swift Testing
- 是否要 app bundle（图标/Info.plist），后续按需
