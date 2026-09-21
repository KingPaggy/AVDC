# AGENTS.md — AVDC_Page 项目记忆

> 来源：原 pi-hermes-memory 项目记忆迁移（2026-09-09）
> 更新：2026-09-21（补 docs/tui 索引，修正 Import Paths）

## 项目指引（合并自原 CLAUDE.md，2026-09-12）


> AI assistant reference for working with this repository.

**⚠️ 全局约束**：Do NOT create git worktrees. Always work
directly in the project root.

## Project Overview

**AVDC** (AV Data Capture) — 抓取 JAV 元数据并整理本地
视频文件的桌面工具，输出供 Emby/Kodi/Plex 使用。

**Stack**: macOS GUI（mac-gui，纯 SwiftUI）+ Python core +
CLI + Go TUI · lxml/BeautifulSoup4、requests/cloudscraper、
Pillow、Baidu AIP
**Python**: 3.13 | **Package manager**: uv | **Workspace**: root
`pyproject.toml` 成员 `core/`、`cli/`（GUI 已归档 .archive/）

## Commands

```bash
uv sync                # Install deps（只能在根目录执行）
# macOS GUI（主力，纯 SwiftUI + Swift Process Bridge）
cd mac-gui && swift build    # 构建（产物 .build/debug/AVDC）
cd mac-gui && swift test     # 测试（Swift Testing，mock CLI）
./mac-gui/.build/debug/AVDC  # 运行（需在项目根 cwd 定位 cli/）
# 其余前端
uv run python cli/cli.py --path /path/to/movies   # Run CLI
uv run pytest core/test cli/test/ -v              # Core/CLI tests
```

## Architecture

```
core/              Business logic (typed, no Qt) — _config,
                   _models, _scraper, _services, _files,
                   _media, _net, _event
mac-gui/           macOS 原生 GUI（主力，纯 SwiftUI）
  Package.swift    SPM（min macOS 26；product 名 = AVDC）
  Sources/AVDCAppCore/  逻辑层：Bridge.swift（Process
                         JSONL）、AppModel.swift（@Observable）、
                         SettingsState.swift
  Sources/AVDCApp/      视图层：AVDCApp/RootView/Home/
                         Tools/Log + SettingsScene（⌘, 窗口）+
                         DesignTokens/Commands/AppInfo/AVDCActions
  Tests/AVDCAppTests/   Bridge/AppModel/Settings 测试
                         （mock_cli.py 离线）
cli/               CLI frontend (no Qt dependency)
tui-go/            Go TUI frontend
.archive/          PySide6/PyQt5 GUI 归档（2026-09-20）
docs/              Documentation（按编号排序，子文件夹按
                   模块分组）
resources/         Icons, screenshots
```

### mac-gui 要点（2026-09-21 重排后）

- 纯 SwiftUI + Swift Process Bridge，**无 ImGui/Metal/ObjC++**
- **部署目标 min macOS 26**（Liquid Glass / ToolbarSpacer
  直用，无 `#available`）；tools-version 6.2 +
  `swiftLanguageModes: [.v5]`
- **侧边栏 3 页**（主页/工具/日志）；设置走独立 `Settings`
  场景（⌘,）；关于走 App 菜单系统 About 面板
- 无 app bundle（决策）：`orderFrontStandardAboutPanel
  (options:)` 传版本；product 名 = AVDC 使 App 菜单显示正常
- 玻璃只用于导航层，自绘玻璃仅主页进度 HUD 一处
- CLT 约束：`@State` 宏不可用（缺 SwiftUIMacros）→ 用
  `@Observable` 单例 + `@Bindable`；XCTest 不可用 → Swift Testing
- Bridge 只认 `cli.py --json-output` JSONL 契约（事件：
  log/progress/success/failure/done + scan `{files,total}`）
- 构建/运行：在项目根 cwd 下（Bridge 向上找 cli/cli.py，
  uv 走绝对路径 /opt/homebrew/bin/uv 不依赖 PATH）
- 设计规范依据：`docs/report-2026-09-21-1016-macGUI-
  官方设计标准对齐优化方案.md`

### mac-gui 模块速查

| 层 | 文件 | 职责 |
|----|------|------|
| Core 逻辑 | `Bridge.swift` | Process 子进程 + JSONL 流式解析、
  stdout/stderr 分离、scan/config/process 封装 |
| Core 状态 | `AppModel.swift` | @Observable 全局：page/home/
  logs(LogEntry)；startProcessing 事件→状态 |
| Core 配置 | `SettingsState.swift` | 10 组 35 字段定义，
  config list 加载 / diff 保存（串行 set）/ reset；搜索过滤 |
| 视图入口 | `AVDCApp.swift` | `Window`（单窗口）+ `Settings`
  场景 + `commands`（⌘1–⌘3/⌘R/⌘./⌘O/⌘E/⌘F/⌘⌥S/⌃⌘F） |
| 视图令牌 | `DesignTokens.swift` | Metric 间距、Page tint/快捷键、
  Palette 语义色、Glass 参数 |
| 视图页面 | `AVDCApp/` 页面 4 文件 | RootView（3 项侧边栏）+
  Home/Tools/Log + SettingsScene（⌘, grouped 表单） |
| 视图支撑 | `AppDelegate.swift` | 无 bundle →
  setActivationPolicy(.regular) + activate()（Dock/菜单栏/快捷键前提）；
  移除 Help 里 Toggle Sidebar 残留；`AVDC_DUMP_MENU=1` 转储菜单 |
| 视图支撑 | `Commands.swift` / `AppInfo.swift` /
  `AVDCActions.swift` | 菜单定义 / 版本与 About 面板 /
  目录选择与日志导出（菜单与工具栏共用） |
| 测试 | `Tests/AVDCAppTests/` | Bridge/AppModel/Settings
  （Swift Testing + mock_cli.py 离线） |

### mac-gui 常见坑（CLT）

- `@State` 不可用 → 局部 UI 状态放 @Observable 模型，
  Binding 手动构造
- 菜单项与工具栏按钮不要重复注册同一 `.keyboardShortcut`
  （菜单已含 ⌘R/⌘./⌘E，按钮只写 `.help` 提示）
- **无 bundle → LaunchServices 把进程登记为 BackgroundOnly**：
  Dock 无图标、菜单栏不归属、菜单快捷键全失效。已修：
  AppDelegate 启动时 `setActivationPolicy(.regular)` + `activate()`
- **SwiftUI 会把系统 Toggle Sidebar 残留到 Help 菜单**：
  AppDelegate 移除 `toggleSidebar:` 项，自己用
  `CommandGroup(replacing: .sidebar)` 提供 ⌘⌥S（状态放模型）
- **快捷键改完验证**：`AVDC_DUMP_MENU=1 ./mac-gui/.build/debug/AVDC`
  打印菜单树（含键位/置灰）后退出
- Swift Testing 宏插件偶发不加载 → Package.swift 手动
  `-plugin-path .../plugins/testing`
- SPM 跨 module 需 public 标注（Core 类型）
- `.insetGrouped` 是 iOS 专属，macOS 用 `.inset`
- organize 模式对无 NFO 文件会走网络刮削并移动文件
  （测试用 mock 项目根，勿对 fixtures 跑真实 organize）

### Docs Structure

```
docs/
├── 00-doc-standards.md          文档写作标准（必读）
├── 01-project-overview.md       项目总览
├── 02-architecture.md           系统架构
├── 03-macos-gui-migration.md    mac-gui 迁移方案
├── 04-tui-lazygit-refactor.md   TUI 重构计划
├── report-*-macGUI-*.md         设计对齐方案 + 执行记录
├── core/                        核心模块
│   ├── 00-overview.md           目录概览
│   ├── 01-requirements.md       I/O 规范
│   └── 02-scraping-flow.md      抓取流程
├── tui/                         TUI 重构文档（d=设计）
│   ├── 00-overview.md           目录概览 + 文档关系
│   ├── d01-phase-plan.md        Phase 0-6 分阶段计划
│   ├── d02-lazygit-architecture.md  lazygit 架构方案
│   ├── d03-lazygit-keybindings.md   lazygit 键位体系
│   ├── d04-avdc-design.md       AVDC 面板/Context 设计
│   └── d05-avdc-keybindings.md  AVDC 各 context 键位表
├── pyside6gui/                  已归档 GUI 参考
│                                （.archive/ 代码，d=设计 / t=踩坑）
│   ├── 00-overview.md           目录概览 + 学习路径
│   ├── d01-architecture.md      整体架构 + 数据流
│   ├── d02-theme-system.md      Theme 常量参考
│   ├── d03-python-models.md     Python 模型层
│   ├── d04-window-and-nav.md    窗口与导航
│   ├── d05-component-library.md 组件库速查
│   ├── d06-animation-and-interaction.md  动画与交互
│   ├── d07-qml-pages.md         QML 页面详解
│   ├── d08-testing.md           测试策略与实践
│   ├── d09-data-binding.md      数据绑定详解
│   ├── d10-accessibility.md     无障碍访问指南
│   ├── d11-internationalization.md 国际化指南
│   ├── d12-qml-conventions.md   QML 代码规范
│   ├── t01-dynamic-property.md  踩坑：动态 Property 陷阱
│   └── t02-debugging-guide.md   踩坑：调试指南
└── tooling/                     工具链
    ├── 00-overview.md           目录概览
    └── 01-codegraph.md          CodeGraph 指南
```

### 📝 文档写作规范

> **写任何文档之前，必须先阅读 [docs/00-doc-standards.md](docs/00-doc-standards.md)。**

所有文档遵循该标准，包括：文件组织（单主题 / 10KB 上限 /
零重叠）、命名规范（`00-` overview / `d` design / `t` trap）、
内容结构（摘要行 / 索引表格）等。

### 🛠️ Edit / Write 工具使用规范

编辑文档时遵循以下原则：

- **优先使用 Edit**：丰富现有文档时，用 Edit 工具精确插入/替换内容，而非重写整个文件
- **Write 只写大纲**：新建文件时，先用 Write 工具创建一个骨架大纲（标题 + 空章节），不要一次写入大量内容
- **渐进式丰富**：通过 Read 工具阅读源码确定要新增的内容，然后每次 Edit 只修改一个细节点
- **小步迭代**：每轮 Edit 聚焦一个具体的知识点或章节，避免一次性大段修改

### Key Modules

| Layer | Key File | Purpose |
|-------|----------|---------|
| Config | `core/_config/config.py` | `AppConfig` — all settings from `config.ini` |
| Models | `core/_models/models.py` | `Movie`, `Actor`, `ProcessResult` dataclasses |
| Orchestrator | `core/_services/orchestrator.py` | `CoreEngine` — batch/single processing entry |
| Scrapers | `core/_scraper/scrapers/*.py` | 7 site scrapers |
| Pipeline | `core/_scraper/scrape_pipeline.py` | Scraper dispatch, `getDataFromJSON` |
| File Utils | `core/_files/file_utils.py` | `getNumber`, `movie_lists` |
| Network | `core/_net/networking.py` | `get_html`, `get_html_javdb` |
| Events | `core/_event/event_bus.py` | `EventBus` cross-component communication |

### Common Import Paths

```python
from core._config.config import AppConfig
from core._services.orchestrator import CoreEngine
from core._event.event_bus import EventBus
from core._models.models import Movie
from core._scraper.scrape_pipeline import getDataFromJSON
from core._files.file_utils import getNumber, movie_lists
from core._net.networking import get_html, get_html_javdb
from core._config.logger import logger, get_log_file_path
from core._config.errors import AVDCError, ScrapingError
```

## Config & Dependencies

**config.ini** sections: `common`, `proxy`, `Name_Rule`,
`update`, `log`, `media`, `escape`, `debug_mode`, `emby`,
`mark`, `uncensored`, `file_download`, `extrafanart`, `baidu`.

> ⚠️ `[emby] api_key` is sensitive. DMM requires Japan proxy.
> JavDB bans IP after ~30 requests.

### Testing

| Directory | Purpose |
|-----------|---------|
| `core/test/unit/` | Unit tests (isolated modules) |
| `core/test/integration/` | Integration tests (component interaction) |
| `core/test/live/` | Live scraper tests (network + video files) |
| `cli/test/` | CLI tests |
| `mac-gui/Tests/` | SwiftUI GUI 测试（Swift Testing，mock CLI 离线） |

Shared fixtures: `core/test/conftest.py`。

> ⚠️ 勿对 `core/test/fixtures/*.mp4` 跑真实 organize——会移动
> 文件并生成 JAV_output/（曾误触发，用 git checkout 恢复）。

## Detailed Documentation

> 按需深入，点击跳转到对应文档。

### 项目级（`docs/` 顶层）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `docs/01-project-overview.md` | 项目总览、技术栈、快速导航 | 首次了解项目 |
| `docs/02-architecture.md` | 系统架构、模块关系图 | 理解整体设计 |
| `docs/03-macos-gui-migration.md` | **mac-gui 迁移方案**（纯 SwiftUI
  选型论证、执行记录、CLI 契约） | mac-gui 开发/维护 |
| `docs/report-2026-09-21-1016-macGUI-官方设计标准对齐优化方案.md` |
  **设计系统对齐方案（决策版 + 执行记录）** | 改 mac-gui 观感/交互前必读 |
| `docs/04-tui-lazygit-refactor.md` | **TUI 重构计划**（lazygit 式
  Window/View/Context 三层，6 阶段） | tui-go 开发/维护 |

### 核心模块（`docs/core/`）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `core/01-requirements.md` | 核心 I/O 黑盒规范 | 修改 core 模块接口 |
| `core/02-scraping-flow.md` | 抓取流程、Pipeline、Scraper Chain | 修改刮削逻辑、添加新站点 |

### PySide6 GUI（`docs/pyside6gui/`，已归档，仅作功能对照参考）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `pyside6gui/d01-architecture.md` | 整体架构、数据流、依赖库、Context Property 注册顺序 | 对照旧 GUI 功能 |
| `pyside6gui/d02-theme-system.md` | Theme 常量、颜色/间距/字号/组件尺寸全量参考 | 对照旧样式 |
| `pyside6gui/d03-python-models.md` | SettingsModel + ProcessingModel + Log 系统 | 对照旧模型层 |
| `pyside6gui/d04-window-and-nav.md` | 无边框窗口、TitleBar、Sidebar、Loader、Toast | 对照旧导航 |
| `pyside6gui/d05-component-library.md` | 组件属性速查、布局规范 | 对照旧组件 |
| `pyside6gui/d06-animation-and-interaction.md` | Behavior 动画、Timer、快捷键 | 对照旧交互 |
| `pyside6gui/d07-qml-pages.md` | 5 个 QML 页面结构 | 对照旧页面 |
| `pyside6gui/d08-testing.md` | 测试架构、Mock 策略 | 对照旧测试 |
| `pyside6gui/d09-data-binding.md` | Python ↔ QML 绑定机制 | 对照旧绑定 |
| `pyside6gui/d10-accessibility.md` | QML Accessible 属性 | 对照旧无障碍 |
| `pyside6gui/d11-internationalization.md` | Qt 国际化 | 对照旧国际化 |
| `pyside6gui/d12-qml-conventions.md` | QML 代码规范 | 对照旧规范 |
| `pyside6gui/d13-modern-qml-page.md` | 现代化页面编写指南 | 对照旧样式 |
| `pyside6gui/t01-dynamic-property.md` | 动态 Property 陷阱 | 对照旧坑 |
| `pyside6gui/t02-debugging-guide.md` | QML 调试指南 | 对照旧调试 |

### TUI 重构（`docs/tui/`）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `tui/00-overview.md` | 目录概览 + 文档关系 | 首次接触 tui-go |
| `tui/d01-phase-plan.md` | Phase 0-6 每阶段动作与验收 | tui-go 阶段开发 |
| `tui/d02-lazygit-architecture.md` | lazygit 包结构/分层/事件循环 | 理解三层架构 |
| `tui/d03-lazygit-keybindings.md` | lazygit 键位组织逻辑 | 键位体系设计 |
| `tui/d04-avdc-design.md` | AVDC 面板/Context/Controller 设计 | AVDC 页面开发 |
| `tui/d05-avdc-keybindings.md` | AVDC 各 context 键位表 | 键位实现 |

### 工具链（`docs/tooling/`）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `tooling/01-codegraph.md` | CodeGraph 代码智能工具指南 | 需要代码导航/影响分析 |

## 待办与未决

- [x] macOS GUI（mac-gui）落地：测试 8/8、依赖清理
- [x] mac-gui 设计系统重排（2026-09-21）：侧边栏 3 页 + ⌘,
  设置窗口 + 系统 About 面板 + 工具栏/菜单/令牌/无障碍降级；
  决策：min macOS 26、不打包 .app
- [ ] mac-gui 人工视觉验证（深浅色 / 无障碍三设置 / 全屏 /
  侧边栏彩色图标）
- [ ] 真实批量刮削验证 Bridge 事件链路稳定性（含长时运行）

## Apple HIG Design

项目遵循 Apple Human Interface Guidelines 平台无关设计原则；
mac-gui 用 SwiftUI 原生控件，观感/无障碍/深浅色系统免费提供
（旧 QML 版参考 docs/pyside6gui/d02-theme-system.md，已归档）。
