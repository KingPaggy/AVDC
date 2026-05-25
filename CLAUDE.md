# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT: Do NOT create git worktrees. Always work directly in the project root directory (`/Users/pageking/Development/09-AVDC_Page/`).**

## Project Overview

AVDC (AV Data Capture) is a Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex. Built with PyQt5, lxml/BeautifulSoup4, requests/cloudscraper, Pillow, and Baidu AIP (face detection).

**Python**: 3.13 (see `.python-version`)

## Common Commands

```bash
uv sync                                        # Install all dependencies (workspace)
uv run python PyQt5-GUI/main.py                # Run PyQt5 GUI
uv run python pyside6_gui/main.py              # Run PySide6 + QML GUI
uv run python cli/cli.py --path /path/to/movies  # Run CLI
uv run pytest core/test cli/test/ -v           # Run all core/CLI tests
uv run pytest pyside6_gui/test/ -v             # Run PySide6 QML tests
uv run pytest pyside6_gui/test/test_theme.py -v  # Single test file
```

UI Development: Qt Designer `*.ui` files compile to `PyQt5-GUI/ui/main_window.py` via `pyuic5-tool`:
```bash
uv run pyuic5 PyQt5-GUI/ui/main_window.ui -o PyQt5-GUI/ui/main_window.py
```

QML lint:
```bash
.venv/bin/pyside6-qmllint pyside6_gui/qml/main.qml
```

## Architecture

### Package Layout

```
cli/                      # CLI frontend (no Qt dependency)
  cli.py                  #   Entry point
  pyproject.toml          #   Workspace member (depends on avdc-core)
  test/                   #   CLI tests
core/                     # ALL business logic (typed, no Qt)
  pyproject.toml          #   Workspace member: avdc-core
  test/                   #   Core test suite (unit, integration, live)
  __init__.py             #   Package docstring only
  _config/                #   AppConfig, logging, errors, settings
  _models/                #   Movie, Actor, ProcessResult
  _scraper/               #   Base, dispatcher, adapter, pipeline
    scrapers/             #   7 scraper implementations
  _services/              #   CoreEngine, metadata, naming, emby_client
  _files/                 #   file_utils, file_operations
  _media/                 #   image_processing (watermarks in _media/watermarks/)
  _net/                   #   networking
  _event/                 #   EventBus, events
tui-go/                   # Go TUI frontend
PyQt5-GUI/                # PyQt5 GUI frontend (legacy)
pyside6_gui/              # PySide6 + QML GUI (new)
  main.py                 #   Entry point: QGuiApplication + QQmlApplicationEngine
  settings_model.py       #   Python data model for QML bindings
  test/                   #   QML test suite
    conftest.py           #     Shared fixtures (qt_app, settings, qml_engine)
    test_theme.py         #     Theme constants validation
    test_settings_model.py # SettingsModel tests
    test_qml_loading.py   #     QML engine loading tests
  qml/                    #   QML files
    main.qml              #     Main window: SplitView + Sidebar + MenuBar
    MacOSSidebar.qml      #     Sidebar navigation component
    HomePage.qml          #     Workspace: file selection + processing
    LogPage.qml           #     Log viewer with filtering
    ToolsPage.qml         #     Tool cards grid
    SettingsPage.qml      #     Settings form
    AboutPage.qml         #     About page
    components/           #     Reusable components
      SectionCard.qml     #       Grouped section container
      ConfigInput.qml     #       Label + TextField
      ConfigSwitch.qml    #       Label + Switch
      ConfigRadioGroup.qml#       Label + Radio buttons
      ConfigSlider.qml    #       Label + Slider + value
      ConfigCheckbox.qml  #       CheckBox + Label
      ConfigFilePicker.qml#       Label + TextField + Browse
      ProgressBar.qml     #       Progress bar + percentage
      StatusBadge.qml     #       Status badge (success/error/warning/info)
      ToolCard.qml        #       Clickable tool card
      LogViewer.qml       #       Scrollable log with level coloring
docs/                     # Documentation
resources/                # Project resources (icons, screenshots)
```

### PySide6 + QML GUI Architecture

**Theme** — Apple HIG 平台无关主题常量，定义在 `pyside6_gui/main.py` 的 `THEME` 字典中，通过 `setContextProperty("Theme", THEME)` 注入 QML。包含：
- Apple HIG 语义化颜色（Dark Mode 默认）
- 8pt 网格间距（spacingXS=4 到 spacingXXXL=32）
- Apple HIG 字号层级（fontMini=10 到 fontStat=28）
- 圆角四级标准（radiusSM=4 到 radiusXL=12）
- 窗口规格、响应式断点、动画时长

**SettingsModel** (`pyside6_gui/settings_model.py`) — Python 数据绑定层，将 `config.ini` 字段暴露为 Qt Properties，支持 QML 双向绑定。每个属性有 `notify` signal，`load()`/`save()`/`resetToDefaults()` 为 `@Slot`。

**数据流**：
```
Python THEME dict ──→ setContextProperty("Theme") ──→ QML 读取
Python SettingsModel ──→ setContextProperty("settings") ──→ QML 双向绑定
```

**导航架构**：`SplitView`（水平分割）+ `MacOSSidebar`（侧边栏导航）+ `Loader`（按需加载页面）。侧边栏理想宽度 240pt，可折叠。

**QML 文件规范**：文件名 PascalCase，类型名与文件名一致。组件文件放在 `qml/components/` 下，通过 `import "components"` 引入。

### CoreEngine (`core/_services/orchestrator.py`)

The main orchestrator for the scrape/organize workflow. Qt-free — accepts `AppConfig` and reports via callbacks (`on_log`, `on_progress`, `on_success`, `on_failure`). Two entry points:

- `process_batch(movie_path, escape_folder, scraper_mode)` — scan directory, process all files
- `process_single(filepath, number, scraper_mode, appoint_url)` — single file

`AppConfig.main_mode` controls scrape vs organize mode. `scraper_mode` controls the scraper/site chain (`1=all`, `2=mgstage`, `3=javbus`, `4=jav321`, `5=javdb/fc2`, `6=avsox`, `7=xcity`, `8=dmm`).

### Import Paths

Import from full subpackage module paths:
```python
from core._config.config import AppConfig
from core._services.orchestrator import CoreEngine
from core._event.event_bus import EventBus
from core._models.models import Movie
from core._scraper.pipeline import getDataFromJSON
from core._files.file_utils import getNumber, movie_lists
from core._files.file_operations import download_file, write_nfo
from core._media.image_processing import add_watermark, cut_poster
from core._net.networking import get_html, get_html_javdb
from core._config.logger import logger, get_log_file_path
from core._config.errors import AVDCError, ScrapingError
```

### Scraper Layer (`core/_scraper/`)

Infrastructure in `core/_scraper/` (base, dispatcher, adapter, pipeline).
Site implementations in `core/_scraper/scrapers/` (avsox, dmm, jav321, javbus, javdb, mgstage, xcity).

Seven scraper modules, each with `main()` + `@register_scraper` subclass:

| Scraper | File | Notes |
|---------|------|-------|
| javbus | `core/_scraper/scrapers/javbus.py` | Primary for censored; also handles uncensored |
| javdb | `core/_scraper/scrapers/javdb.py` | Primary for FC2; uses cloudscraper for CF bypass |
| jav321 | `core/_scraper/scrapers/jav321.py` | Fallback |
| avsox | `core/_scraper/scrapers/avsox.py` | Fallback |
| dmm | `core/_scraper/scrapers/dmm.py` | Requires Japan proxy |
| mgstage | `core/_scraper/scrapers/mgstage.py` | Primary for mgstage/amateur patterns |
| xcity | `core/_scraper/scrapers/xcity.py` | Fallback |

All scrapers discovered via `ScraperRegistry` + `@register_scraper`, dispatched by `ScraperDispatcher`.

### Number Pattern Classification

| Pattern | Example | Scraper chain |
|---------|---------|---------------|
| Uncensored | `111111-1111`, `HEYZO-1111`, `n1111` | javbus (uncensored) → javdb → jav321 → avsox |
| FC2 | `FC2-111111`, `FC2-PPV-111111` | javdb |
| Mgstage/amateur | `259LUXU-1111`, `SIRO-1234` | mgstage → jav321 → javdb → javbus |
| DMM style | `ssni00111` (no separator) | dmm |
| European | `sexart.19.11.03` | javdb (US) → javbus (US) |
| Standard censored | `SSIS-123`, `ABP-456` | javbus → jav321 → xcity → javdb → avsox |

### Testing

Tests use pytest, organized into three areas:

| Directory | Purpose |
|-----------|---------|
| `core/test/unit/` | Core unit tests (isolated modules) |
| `core/test/integration/` | Integration tests (component interaction) |
| `core/test/live/` | Live scraper tests (require network + video files) |
| `cli/test/` | CLI tests |
| `pyside6_gui/test/` | PySide6 QML tests (40 tests) |

Key test files:
- `core/test/unit/test_core.py` — Core logic tests (largest file)
- `core/test/unit/test_core_engine.py` — CoreEngine batch/single processing
- `core/test/unit/test_scraper_dispatcher.py` — Scraper dispatch logic
- `core/test/live/scrape_test.py`, `core/test/live/test_real_scrape.py` — Live scraper tests
- `pyside6_gui/test/test_theme.py` — Theme constants (16 tests, no Qt needed)
- `pyside6_gui/test/test_settings_model.py` — SettingsModel Properties/Signals/Slots (20 tests)
- `pyside6_gui/test/test_qml_loading.py` — QML engine loading (4 tests, needs Qt)

PySide6 tests auto-set `QT_QPA_PLATFORM=offscreen` via `conftest.py`. Run with:
```bash
uv run pytest pyside6_gui/test/ -v
```

Shared fixtures in `core/test/conftest.py`: `tmp_dir`, `tmp_log_dir`, `tmp_config_ini`.
Shared fixtures in `pyside6_gui/test/conftest.py`: `qt_app`, `tmp_config_ini`, `settings`, `qml_engine`.

### Proxy Requirements

- DMM requires Japan proxy
- JavDB bans IP after ~30 requests — use proxies or rotate
- `get_html_javdb()` bypasses Cloudflare via cloudscraper
- Proxy config in `config.ini [proxy]` section

### Adding New Scrapers

1. Create `core/_scraper/scrapers/newsite.py`, subclass `ScraperBase`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `core/_scraper/scraper_dispatcher.py` `SCRAPER_MAPPING`
4. Add import in `core/_scraper/scrape_pipeline.py` `get_scraper_modules()`

## Config

`config.ini` sections: common, proxy, Name_Rule, update, log, media, escape, debug_mode, emby, mark, uncensored, file_download, extrafanart, baidu. **Note**: `[emby] api_key` is sensitive.

## Reference Documents

- `docs/requirements.md` — Core I/O contract (what the engine receives and produces)
- `docs/architecture.md` — System architecture overview
- `docs/scraping-flow.md` — Scraping workflow and pipeline details
- `docs/qml-ui-design.md` — QML UI design manual (colors, typography, components, interaction)
- `/Users/pageking/Development/24-MacOS26-设计规范/设计原则-平台无关/` — Apple HIG platform-independent design principles

## Entry Points

- `PyQt5-GUI/main.py` — PyQt5 GUI: `uv run python PyQt5-GUI/main.py`
- `pyside6_gui/main.py` — PySide6 + QML GUI: `uv run python pyside6_gui/main.py`
- `cli/cli.py` — Standalone CLI (no Qt dependency): `uv run python cli/cli.py --path /path/to/movies`

## Dependency Management (uv workspace)

Root `pyproject.toml` declares a workspace with four members:
- **core/** (`avdc-core`) — core business logic dependencies
- **cli/** (`avdc-cli`) — depends on avdc-core, no additional deps
- **PyQt5-GUI/** (`avdc-pyqt5-gui`) — depends on avdc-core + pyqt5/pyuic5-tool
- **pyside6_gui/** (`avdc-pyside6-gui`) — depends on pyside6 + avdc-core

All dependencies are installed via `uv sync` into a single `.venv` at root. **Only run `uv sync` from the project root**, never from subdirectories — workspace members share one `.venv`, subdirectory `uv sync` will overwrite conflicting packages.

## 工作流规范：主 Agent 审查 + 子 Agent 编辑

**原则**：主 Agent 只负责规划、审查和决策，所有代码编辑任务交给子 Agent 执行。

### 执行流程

1. **主 Agent**：制定计划，明确每个文件的改动内容
2. **主 Agent**：启动子 Agent（`subagent_type: "claude"`），给出精确的编辑指令（包含文件路径、行号、旧代码/新代码）
3. **子 Agent**：读取文件 → 执行 Edit → 运行测试 → 报告结果
4. **主 Agent**：审查子 Agent 的改动结果（Read 关键文件确认），确认测试通过

### 适用场景

- 任何涉及文件编辑的任务（代码修改、新增文件、删除代码）
- 多文件批量改动（按阶段分别启动子 Agent）
- 重构、优化、Bug 修复

### 不适用场景

- 纯信息查询（直接用 Bash/grep/Read）
- 运行测试、构建、启动服务（直接用 Bash）
- 制定计划、设计方案（主 Agent 自己完成）

## Git Commit Convention

采用 Emoji + Conventional Commits 风格。格式：`emoji type(scope): description`

常用 emoji：`🐛 fix` `♻️ refactor` `✨ feat` `📦 chore` `📝 docs` `🚚 refactor` `🔧 chore` `🧪 test`

示例：`🐛 fix(pyside6-gui): 修复 Theme 单例注册`

Co-Authored-By 行格式：
```
Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
