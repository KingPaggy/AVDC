# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT: Do NOT create git worktrees. Always work directly in the project root directory (`/Users/pageking/Development/09-AVDC_Page/`).**

## Project Overview

AVDC (AV Data Capture) is a Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex. Built with PyQt5, lxml/BeautifulSoup4, requests/cloudscraper, Pillow, and Baidu AIP (face detection).

**Python**: 3.13 (see `.python-version`)

## Common Commands

```bash
uv sync                                        # Install all dependencies (workspace)
uv run python pyside6_gui/main.py              # Run PySide6 + QML GUI (primary)
uv run python PyQt5-GUI/main.py                # Run PyQt5 GUI (legacy)
uv run python cli/cli.py --path /path/to/movies  # Run CLI
uv run pytest core/test cli/test/ -v           # Run core/CLI tests
uv run pytest pyside6_gui/test/ -v             # Run PySide6 QML tests
```

QML lint: `.venv/bin/pyside6-qmllint pyside6_gui/qml/main.qml`
UI compile: `uv run pyuic5 PyQt5-GUI/ui/main_window.ui -o PyQt5-GUI/ui/main_window.py`

## Architecture

### Package Layout

```
core/              Business logic (typed, no Qt) — _config, _models, _scraper, _services, _files, _media, _net, _event
pyside6_gui/       PySide6 + QML GUI (primary frontend) — main.py, settings_model.py, qml/
PyQt5-GUI/         PyQt5 GUI (legacy frontend)
cli/               CLI frontend (no Qt dependency)
tui-go/            Go TUI frontend
docs/              Documentation
resources/         Icons, screenshots
```

### Key Modules

| Layer | Key Files | Purpose |
|-------|-----------|---------|
| Config | `core/_config/config.py` | `AppConfig` — all settings, loaded from `config.ini` |
| Models | `core/_models/models.py` | `Movie`, `Actor`, `ProcessResult` dataclasses |
| Orchestrator | `core/_services/orchestrator.py` | `CoreEngine` — batch/single processing entry point |
| Scrapers | `core/_scraper/scrapers/*.py` | 7 site scrapers (javbus, javdb, jav321, avsox, dmm, mgstage, xcity) |
| Pipeline | `core/_scraper/scrape_pipeline.py` | Scraper dispatch, `getDataFromJSON` |
| File Utils | `core/_files/file_utils.py` | `getNumber`, `movie_lists` |
| Network | `core/_net/networking.py` | `get_html`, `get_html_javdb` (cloudscraper) |
| Events | `core/_event/event_bus.py` | `EventBus` for cross-component communication |

### Import Paths

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

### CoreEngine

`CoreEngine` in `core/_services/orchestrator.py` — Qt-free orchestrator accepting `AppConfig` + callback reporting (`on_log`, `on_progress`, `on_success`, `on_failure`).

- `process_batch(movie_path, escape_folder, scraper_mode)` — scan directory, process all files
- `process_single(filepath, number, scraper_mode, appoint_url)` — single file

`AppConfig.main_mode` controls scrape vs organize mode. `scraper_mode`: `1=all`, `2=mgstage`, `3=javbus`, `4=jav321`, `5=javdb/fc2`, `6=avsox`, `7=xcity`, `8=dmm`.

### Scraper Dispatch

Scrapers registered via `@register_scraper` + `ScraperRegistry`, dispatched by `ScraperDispatcher`. Number pattern classification:

| Pattern | Example | Scraper chain |
|---------|---------|---------------|
| Standard censored | `SSIS-123`, `ABP-456` | javbus → jav321 → xcity → javdb → avsox |
| Uncensored | `111111-1111`, `HEYZO-1111` | javbus (uncensored) → javdb → jav321 → avsox |
| FC2 | `FC2-111111` | javdb |
| Mgstage/amateur | `259LUXU-1111`, `SIRO-1234` | mgstage → jav321 → javdb → javbus |
| DMM style | `ssni00111` (no separator) | dmm |
| European | `sexart.19.11.03` | javdb (US) → javbus (US) |

### Adding New Scrapers

1. Create `core/_scraper/scrapers/newsite.py`, subclass `ScraperBase`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `core/_scraper/scraper_dispatcher.py` `SCRAPER_MAPPING`
4. Add import in `core/_scraper/scrape_pipeline.py` `get_scraper_modules()`

### PySide6 + QML GUI

**Theme** — Apple HIG constants in `pyside6_gui/main.py` `THEME` dict, injected via `setContextProperty("Theme", THEME)`.

**SettingsModel** (`pyside6_gui/settings_model.py`) — Qt Properties for `config.ini` fields, QML双向绑定. `load()`/`save()`/`resetToDefaults()` are `@Slot`.

**Data flow**:
```
Python THEME dict ──→ setContextProperty("Theme") ──→ QML read
Python SettingsModel ──→ setContextProperty("settings") ──→ QML two-way binding
```

**Navigation**: `SplitView` + `MacOSSidebar` + `Loader` (lazy page loading). Sidebar target width 240pt, collapsible.

**QML convention**: PascalCase filenames, type name matches filename. Components in `qml/components/`, imported via `import "components"`.

### Dependency Management (uv workspace)

Root `pyproject.toml` declares workspace with four members: `core/` (avdc-core), `cli/` (avdc-cli), `PyQt5-GUI/` (avdc-pyqt5-gui), `pyside6_gui/` (avdc-pyside6-gui).

All deps installed via `uv sync` into single `.venv` at root. **Only run `uv sync` from project root** — workspace members share one `.venv`.

### Config

`config.ini` sections: common, proxy, Name_Rule, update, log, media, escape, debug_mode, emby, mark, uncensored, file_download, extrafanart, baidu. **Note**: `[emby] api_key` is sensitive. DMM requires Japan proxy. JavDB bans IP after ~30 requests.

### Testing

| Directory | Purpose |
|-----------|---------|
| `core/test/unit/` | Core unit tests (isolated modules) |
| `core/test/integration/` | Integration tests (component interaction) |
| `core/test/live/` | Live scraper tests (network + video files) |
| `cli/test/` | CLI tests |
| `pyside6_gui/test/` | PySide6 QML tests (auto-set `QT_QPA_PLATFORM=offscreen`) |

Shared fixtures: `core/test/conftest.py` (`tmp_dir`, `tmp_log_dir`, `tmp_config_ini`), `pyside6_gui/test/conftest.py` (`qt_app`, `tmp_config_ini`, `settings`, `qml_engine`).

## Reference Documents

- `docs/requirements.md` — Core I/O contract
- `docs/architecture.md` — System architecture overview
- `docs/scraping-flow.md` — Scraping workflow and pipeline details
- `docs/qml-ui-design.md` — QML UI design manual
- `/Users/pageking/Development/24-MacOS26-设计规范/设计原则-平台无关/` — Apple HIG platform-independent design principles

## CodeGraph

CodeGraph v0.9.4 is installed for code intelligence. Index updated via `codegraph index .`. Useful commands:

```bash
codegraph status .                          # Index status
codegraph query "SymbolName"                 # Search symbols
codegraph callers "methodName"               # Find callers of a symbol
codegraph callees "methodName"               # Find what a symbol calls
codegraph impact "methodName"                # Analyze affected code by changing a symbol
codegraph context "Add feature X"            # Build context for a task (outputs markdown)
codegraph files                             # Show project file structure from index
codegraph sync .                             # Sync changes since last index
```
