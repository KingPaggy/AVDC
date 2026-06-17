# AVDC — Project Guide

> AI assistant reference for working with this repository.

**⚠️ 全局约束**：Do NOT create git worktrees. Always work directly in the project root.

## Project Overview

**AVDC** (AV Data Capture) — Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex.

**Stack**: PyQt5/PySide6 + QML, lxml/BeautifulSoup4, requests/cloudscraper, Pillow, Baidu AIP
**Python**: 3.13 | **Package manager**: uv | **Workspace**: root `pyproject.toml` with 4 members (`core/`, `cli/`, `pyqt5-gui/`, `pyside6_gui/`)

## Commands

```bash
uv sync                                              # Install deps（只能在根目录执行）
uv run python pyside6_gui/main.py                    # Run PySide6 + QML GUI（primary）
uv run python pyqt5-gui/main.py                      # Run PyQt5 GUI（legacy）
uv run python cli/cli.py --path /path/to/movies      # Run CLI
uv run pytest core/test cli/test/ -v                 # Core/CLI tests
uv run pytest pyside6_gui/test/ -v                   # PySide6 QML tests
.venv/bin/pyside6-qmllint pyside6_gui/qml/main.qml  # QML lint
```

## Architecture

```
core/              Business logic (typed, no Qt) — _config, _models, _scraper, _services, _files, _media, _net, _event
pyside6_gui/       PySide6 + QML GUI (primary frontend)
pyqt5-gui/         PyQt5 GUI (legacy frontend)
cli/               CLI frontend (no Qt dependency)
tui-go/            Go TUI frontend
docs/              Documentation
```

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

| 文档 | 内容 | 何时阅读 |
|------|------|----------|
| [docs/01-project-overview.md](docs/01-project-overview.md) | 项目总览、技术栈、快速导航 | 首次了解项目 |
| [docs/02-architecture.md](docs/02-architecture.md) | 系统架构、模块关系图 | 理解整体设计 |
| [docs/core/02-scraping-flow.md](docs/core/02-scraping-flow.md) | 抓取流程、Pipeline、Scraper Chain、新增刮削器步骤 | 修改刮削逻辑、添加新站点 |
| [docs/core/01-requirements.md](docs/core/01-requirements.md) | 核心模块 I/O 规范 | 修改 core 模块接口 |
| [docs/pyside6gui/01-qml-ui-design.md](docs/pyside6gui/01-qml-ui-design.md) | QML 组件规范、布局模式、Theme、SectionCard 模式 | 开发 QML 页面/组件 |
| [docs/pyside6gui/02-dynamic-property.md](docs/pyside6gui/02-dynamic-property.md) | PySide6 动态 Property 陷阱与解决方案 | 修改 SettingsModel |
| [docs/tooling/01-codegraph.md](docs/tooling/01-codegraph.md) | CodeGraph 代码智能工具使用指南 | 需要代码导航/影响分析 |

## Apple HIG Design

项目遵循 Apple Human Interface Guidelines 平台无关设计原则，详见 [docs/pyside6gui/01-qml-ui-design.md](docs/pyside6gui/01-qml-ui-design.md)。
