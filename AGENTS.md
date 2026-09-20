# AGENTS.md — AVDC_Page 项目记忆

> 来源：原 pi-hermes-memory 项目记忆迁移（2026-09-09）
> 相关：QML 布局坑已入全局踩坑合集

## THEME 字典字体属性命名

- 字体族：fontFamilySans / fontFamilyDisplay / fontFamilyMono
- 字重：weightLight ~ weightBold
- 行高：lineHeightTight / Normal / Relaxed
- 字间距：letterSpacingTight / Normal / Wide
- QML 引用：`font.family: Theme.fontFamilySans`、`font.weight:
  Theme.weightSemibold`
- ⚠️ 必须用 `font.letterSpacing`，不是顶层属性

## 文档组织

- docs/ 文档组织与丰富工作流（编号前缀、Edit 优先、AGENTS.md
  精简索引）见项目 AGENTS.md 与 docs/
- QML 布局陷阱已迁全局踩坑合集

---

## 项目指引（合并自原 CLAUDE.md，2026-09-12）


> AI assistant reference for working with this repository.

**⚠️ 全局约束**：Do NOT create git worktrees. Always work directly in the project root.

## Project Overview

**AVDC** (AV Data Capture) — Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex.

**Stack**: SwiftUI（mac-gui 主力前端）· Python core + CLI · lxml/BeautifulSoup4、requests/cloudscraper、Pillow、Baidu AIP
**Python**: 3.13 | **Package manager**: uv | **Workspace**: root `pyproject.toml` 成员 `core/`、`cli/`（GUI 已归档）

## Commands

```bash
uv sync                                              # Install deps（只能在根目录执行）
# macOS GUI（主力，纯 SwiftUI + Swift Process Bridge）
cd mac-gui && swift build                            # 构建
cd mac-gui && swift test                             # 测试（Swift Testing，mock CLI）
./mac-gui/.build/debug/AVDCApp                       # 运行（需在项目根，cwd 定位 cli/）
# 其余前端
uv run python cli/cli.py --path /path/to/movies      # Run CLI
uv run pytest core/test cli/test/ -v                 # Core/CLI tests
```

## Architecture

```
core/              Business logic (typed, no Qt) — _config, _models, _scraper, _services, _files, _media, _net, _event
mac-gui/           macOS 原生 GUI（主力，纯 SwiftUI）
  Package.swift    SPM（swift build / swift test）
  Sources/AVDCAppCore/  逻辑层：Bridge.swift（Process JSONL）、AppModel.swift（@Observable）、SettingsState.swift
  Sources/AVDCApp/      视图层：AVDCApp/RootView/Home/Settings/Tools/Log/About
  Tests/AVDCAppTests/   Bridge/AppModel/Settings 测试（mock_cli.py 离线）
cli/               CLI frontend (no Qt dependency)
tui-go/            Go TUI frontend
.archive/          PySide6/PyQt5 GUI 归档（2026-09-20）
docs/              Documentation（按编号排序，子文件夹按模块分组）
resources/         Icons, screenshots
```

### mac-gui 要点（2026-09-20 落地）

- 纯 SwiftUI + Swift Process Bridge，**无 ImGui/Metal/ObjC++**
- CLT 约束：`@State` 宏不可用（缺 SwiftUIMacros）→ 用
  `@Observable` 单例 + `@Bindable`；XCTest 不可用 → Swift Testing
- Bridge 只认 `cli.py --json-output` JSONL 契约（4.3 契约隔离）
- 5 页全部完成：Home/Settings/Tools/Log/About；测试 8/8 通过
- 构建在项目根 cwd 下运行（Bridge 向上找 cli/cli.py + uv 绝对路径）

### Docs Structure

```
docs/
├── 00-doc-standards.md          文档写作标准（必读）
├── 01-project-overview.md       项目总览
├── 02-architecture.md           系统架构
├── core/                        核心模块
│   ├── 00-overview.md           目录概览
│   ├── 01-requirements.md       I/O 规范
│   └── 02-scraping-flow.md      抓取流程
├── pyside6gui/                  PySide6 GUI（d=设计 / t=踩坑）
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

所有文档遵循该标准，包括：文件组织（单主题 / 10KB 上限 / 零重叠）、命名规范（`00-` overview / `d` design / `t` trap）、内容结构（摘要行 / 索引表格）等。

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
from core._scraper.pipeline import getDataFromJSON
from core._files.file_utils import getNumber, movie_lists
from core._net.networking import get_html, get_html_javdb
from core._config.logger import logger, get_log_file_path
from core._config.errors import AVDCError, ScrapingError
```

## Config & Dependencies

**config.ini** sections: `common`, `proxy`, `Name_Rule`, `update`, `log`, `media`, `escape`, `debug_mode`, `emby`, `mark`, `uncensored`, `file_download`, `extrafanart`, `baidu`.

> ⚠️ `[emby] api_key` is sensitive. DMM requires Japan proxy. JavDB bans IP after ~30 requests.

### Testing

| Directory | Purpose |
|-----------|---------|
| `core/test/unit/` | Unit tests (isolated modules) |
| `core/test/integration/` | Integration tests (component interaction) |
| `core/test/live/` | Live scraper tests (network + video files) |
| `cli/test/` | CLI tests |
| `pyside6_gui/test/` | QML tests (auto-set `QT_QPA_PLATFORM=offscreen`) |

Shared fixtures: `core/test/conftest.py`, `pyside6_gui/test/conftest.py`.

## Detailed Documentation

> 按需深入，点击跳转到对应文档。

### 项目级（`docs/` 顶层）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `docs/01-project-overview.md` | 项目总览、技术栈、快速导航 | 首次了解项目 |
| `docs/02-architecture.md` | 系统架构、模块关系图 | 理解整体设计 |

### 核心模块（`docs/core/`）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `core/01-requirements.md` | 核心 I/O 黑盒规范 | 修改 core 模块接口 |
| `core/02-scraping-flow.md` | 抓取流程、Pipeline、Scraper Chain | 修改刮削逻辑、添加新站点 |

### PySide6 GUI（`docs/pyside6gui/`）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `pyside6gui/d01-architecture.md` | 整体架构、数据流、依赖库、Context Property 注册顺序 | 首次接触 GUI 代码 |
| `pyside6gui/d02-theme-system.md` | Theme 常量、颜色/间距/字号/组件尺寸全量参考 | 调整视觉样式 |
| `pyside6gui/d03-python-models.md` | SettingsModel + ProcessingModel + Log 系统 | 修改 Python 模型层 |
| `pyside6gui/d04-window-and-nav.md` | 无边框窗口、TitleBar、Sidebar、Loader、Toast | 修改窗口/导航 |
| `pyside6gui/d05-component-library.md` | 组件属性速查、布局规范、新增组件步骤 | 开发 QML 页面/组件 |
| `pyside6gui/d06-animation-and-interaction.md` | Behavior 动画、Timer、快捷键、状态过渡 | 添加动画/交互 |
| `pyside6gui/d07-qml-pages.md` | 5 个 QML 页面的结构、数据绑定、交互流程 | 开发/调试页面逻辑 |
| `pyside6gui/d08-testing.md` | 测试架构、Mock 策略、QML 测试、截图回归 | 添加/运行 GUI 测试 |
| `pyside6gui/d09-data-binding.md` | Python ↔ QML 绑定机制、Signal/Property、调试技巧 | 修改数据绑定 |
| `pyside6gui/d10-accessibility.md` | QML Accessible 属性、键盘导航、屏幕阅读器 | 添加无障碍支持 |
| `pyside6gui/d11-internationalization.md` | Qt 国际化、qsTr()、翻译工作流 | 添加多语言支持 |
| `pyside6gui/d12-qml-conventions.md` | QML 代码规范（命名、布局、import） | 编写 QML 代码 |
| `pyside6gui/d13-modern-qml-page.md` | 现代化页面编写指南（样式、动画、性能） | 编写现代化 QML 页面 |
| `pyside6gui/t01-dynamic-property.md` | 动态 Property 陷阱与类工厂解法 | 修改 SettingsModel |
| `pyside6gui/t02-debugging-guide.md` | QML 控制台错误、日志调试、性能分析 | 调试 GUI 问题 |

### 工具链（`docs/tooling/`）

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| `tooling/01-codegraph.md` | CodeGraph 代码智能工具指南 | 需要代码导航/影响分析 |

## Apple HIG Design

项目遵循 Apple Human Interface Guidelines 平台无关设计原则，详见 [docs/pyside6gui/d02-theme-system.md](docs/pyside6gui/d02-theme-system.md)。
