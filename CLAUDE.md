# AVDC — Project Guide

> AI assistant reference for working with this repository.

**IMPORTANT: Do NOT create git worktrees. Always work directly in the project root.**

## Quick Navigation

- [Commands & Testing](#common-commands)
- [Architecture Overview](#architecture-overview)
- [CoreEngine & Scraper System](#coreengine--scraper-system)
- [PySide6 + QML GUI](#pyside6--qml-gui)
- [Config & Dependencies](#config--dependencies)
- [CodeGraph Tooling](#codegraph-tooling)
- [Reference Documents](#reference-documents)

## Project Overview

**AVDC** (AV Data Capture) — Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex.

**Stack**: PyQt5/PySide6 + QML, lxml/BeautifulSoup4, requests/cloudscraper, Pillow, Baidu AIP (face detection)
**Python**: 3.13 (see `.python-version`)

## Common Commands

```bash
uv sync                                        # Install deps (run from project root)
uv run python pyside6_gui/main.py              # Run PySide6 + QML GUI (primary)
uv run python pyqt5-gui/main.py                # Run PyQt5 GUI (legacy)
uv run python cli/cli.py --path /path/to/movies  # Run CLI
uv run pytest core/test cli/test/ -v           # Core/CLI tests
uv run pytest pyside6_gui/test/ -v             # PySide6 QML tests
```

```bash
# QML lint
.venv/bin/pyside6-qmllint pyside6_gui/qml/main.qml
# UI compile
uv run pyuic5 pyqt5-gui/ui/main_window.ui -o pyqt5-gui/ui/main_window.py
```

## Architecture Overview

### Package Layout

```
core/              Business logic (typed, no Qt) — _config, _models, _scraper, _services, _files, _media, _net, _event
pyside6_gui/       PySide6 + QML GUI (primary frontend)
pyqt5-gui/         PyQt5 GUI (legacy frontend)
cli/               CLI frontend (no Qt dependency)
tui-go/            Go TUI frontend
docs/              Documentation
resources/         Icons, screenshots
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

## CoreEngine & Scraper System

### CoreEngine

Located in `core/_services/orchestrator.py`. Qt-free orchestrator accepting `AppConfig` + callbacks (`on_log`, `on_progress`, `on_success`, `on_failure`).

- `process_batch(movie_path, escape_folder, scraper_mode)` — scan directory, process all files
- `process_single(filepath, number, scraper_mode, appoint_url)` — single file

`AppConfig.main_mode` controls scrape vs organize mode.
`scraper_mode`: `1=all`, `2=mgstage`, `3=javbus`, `4=jav321`, `5=javdb/fc2`, `6=avsox`, `7=xcity`, `8=dmm`.

### Scraper Dispatch

Scrapers registered via `@register_scraper` + `ScraperRegistry`, dispatched by `ScraperDispatcher`.

| Pattern | Example | Scraper Chain |
|---------|---------|---------------|
| Standard censored | `SSIS-123` | javbus → jav321 → xcity → javdb → avsox |
| Uncensored | `111111-1111` | javbus (uncensored) → javdb → jav321 → avsox |
| FC2 | `FC2-111111` | javdb |
| Mgstage/amateur | `259LUXU-1111` | mgstage → jav321 → javdb → javbus |
| DMM style | `ssni00111` (no separator) | dmm |
| European | `sexart.19.11.03` | javdb (US) → javbus (US) |

### Adding New Scrapers

1. Create `core/_scraper/scrapers/newsite.py`, subclass `ScraperBase`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `core/_scraper/scraper_dispatcher.py` `SCRAPER_MAPPING`
4. Add import in `core/_scraper/scrape_pipeline.py` `get_scraper_modules()`

## PySide6 + QML GUI

### Theme & Settings

- **Theme** — Apple HIG constants in `pyside6_gui/main.py` `THEME` dict, injected via `setContextProperty("Theme", THEME)`
- **SettingsModel** (`pyside6_gui/settings_model.py`) — Qt Properties for `config.ini` fields, QML two-way binding. `load()`/`save()`/`resetToDefaults()` are `@Slot`

### Data Flow

```
Python THEME dict ──→ setContextProperty("Theme") ──→ QML read
Python SettingsModel ──→ setContextProperty("settings") ──→ QML two-way binding
```

### Navigation

`SplitView` + `MacOSSidebar` + `Loader` (lazy page loading). Sidebar target width 240pt, collapsible.

### QML Conventions

- PascalCase filenames, type name matches filename
- Components in `qml/components/`, imported via `import "components"`

### Layout Types

| Type | Child Properties | Notes |
|------|------------------|-------|
| `ColumnLayout` / `RowLayout` / `GridLayout` | `Layout.*` (`Layout.fillWidth`, `Layout.preferredHeight`) | Auto-sizing |
| `Column` / `Row` | `implicitHeight`/`implicitWidth` or explicit `width`/`height` | **Cannot** use `Layout.*` |
| `Item` / `Rectangle` | Explicit dimensions or child `implicitHeight` | Basic types |

### implicitHeight Key Concept

- Non-Layout parents (e.g., `Column`) depend on children's `implicitHeight` for their own size
- If children lack `implicitHeight` and explicit `height`, parent height = 0, content invisible
- `anchors.fill: parent` on a zero-size parent creates circular dependency → layout failure

### SectionCard Pattern

```qml
Rectangle {
    id: root
    implicitHeight: contentColumn.implicitHeight + padding
    default property alias contentData: contentColumn.children

    ColumnLayout {
        id: contentColumn
        width: parent.width - padding
        x: padding / y: padding
    }
}
```

### Page Layout Pattern (`ScrollView > Column > SectionCard`)

```qml
ScrollView {
    Column {
        width: Math.min(parent.width - Theme.spacingXL * 2, Theme.maxContentWidth)
        spacing: Theme.spacingLG
        Item { implicitHeight: Theme.spacingXL }  // Top spacer
        SectionCard { ... }
        SectionCard { ... }
        Item { implicitHeight: Theme.spacingXL }  // Bottom spacer
    }
}
```

## Config & Dependencies

### uv Workspace

Root `pyproject.toml` declares workspace with four members: `core/` (avdc-core), `cli/` (avdc-cli), `pyqt5-gui/` (avdc-pyqt5-gui), `pyside6_gui/` (avdc-pyside6-gui).

All deps installed via `uv sync` into single `.venv` at root. **Only run `uv sync` from project root.**

### config.ini

Sections: `common`, `proxy`, `Name_Rule`, `update`, `log`, `media`, `escape`, `debug_mode`, `emby`, `mark`, `uncensored`, `file_download`, `extrafanart`, `baidu`.

> ⚠️ `[emby] api_key` is sensitive. DMM requires Japan proxy. JavDB bans IP after ~30 requests.

### Testing

| Directory | Purpose |
|-----------|---------|
| `core/test/unit/` | Unit tests (isolated modules) |
| `core/test/integration/` | Integration tests (component interaction) |
| `core/test/live/` | Live scraper tests (network + video files) |
| `cli/test/` | CLI tests |
| `pyside6_gui/test/` | QML tests (auto-set `QT_QPA_PLATFORM=offscreen`) |

Shared fixtures: `core/test/conftest.py` (`tmp_dir`, `tmp_log_dir`, `tmp_config_ini`), `pyside6_gui/test/conftest.py` (`qt_app`, `tmp_config_ini`, `settings`, `qml_engine`).

## CodeGraph Tooling

CodeGraph v0.9.4 is the primary code intelligence tool for this project.
Keep index fresh: `codegraph sync .`

### Decision Tree

| If you need... | Use |
|----------------|-----|
| Find a symbol definition | `codegraph query "SymbolName"` |
| Find callers of a function | `codegraph callers "methodName"` |
| Find callees of a function | `codegraph callees "methodName"` |
| Assess change impact | `codegraph impact "SymbolName"` |
| Collect files for a task | `codegraph context "task description"` |
| Browse project structure | `codegraph files` |
| Check index freshness | `codegraph status .` |

### When NOT to use CodeGraph

- **Known file path** → Use `read` directly
- **Search text/comments** → Use `grep` via Bash
- **File pattern matching** → Use `find` via Bash
- **Index is stale** → Run `codegraph sync .` first

### Task-Specific Tips

- Modifying `CoreEngine` → `codegraph impact "CoreEngine"` to assess scope
- Adding scrapers → `codegraph context "add scraper X"` to collect context
- Unsure where files are → `codegraph files` to see indexed structure

## Reference Documents

- `docs/requirements.md` — Core I/O contract
- `docs/architecture.md` — System architecture overview
- `docs/scraping-flow.md` — Scraping workflow and pipeline details
- `docs/qml-ui-design.md` — QML UI design manual
- Apple HIG platform-independent design principles (local)
