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
uv run python cli/cli.py --path /path/to/movies  # Run CLI
uv run pytest core/test cli/test/ -v           # Run all tests
uv run pytest core/test/unit/test_core_engine.py -v # Single test file
```

UI Development: Qt Designer `*.ui` files compile to `PyQt5-GUI/ui/main_window.py` via `pyuic5-tool`:
```bash
uv run pyuic5 PyQt5-GUI/ui/main_window.ui -o PyQt5-GUI/ui/main_window.py
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
    conftest.py           #   Shared fixtures
  __init__.py             #   Package docstring only
  _config/                #   AppConfig, logging, errors, settings
  _models/                #   Movie, Actor, ProcessResult
  _scraper/               #   Base, dispatcher, adapter, pipeline
    scrapers/             #   7 scraper implementations
      avsox.py, dmm.py, jav321.py, javbus.py, javdb.py, mgstage.py, xcity.py
  _services/              #   CoreEngine, metadata, naming, emby_client
  _files/                 #   file_utils, file_operations
  _media/                 #   image_processing (watermarks in _media/watermarks/)
  _net/                   #   networking
  _event/                 #   EventBus, events
tui-go/                   # Go TUI frontend
PyQt5-GUI/                # PyQt5 GUI frontend
  main.py                 #   UI layer: PyQt5 display + event handling
  ui/                     #   Compiled PyQt5 UI from Qt Designer
  resources/              #   GUI-only assets (icons, screenshots)
  docs/                   #   UI-specific documentation
docs/                     # Documentation: architecture, requirements, scraping-flow
resources/                # Project resources (icons, screenshots)

### CoreEngine (`core/_services/orchestrator.py`)

The main orchestrator for the scrape/organize workflow. Qt-free — accepts `AppConfig` and reports via callbacks (`on_log`, `on_progress`, `on_success`, `on_failure`). Two entry points:

- `process_batch(movie_path, escape_folder, scraper_mode)` — scan directory, process all files
- `process_single(filepath, number, scraper_mode, appoint_url)` — single file

`AppConfig.main_mode` controls scrape vs organize mode. `scraper_mode` controls the scraper/site chain (`1=all`, `2=mgstage`, `3=javbus`, `4=jav321`, `5=javdb/fc2`, `6=avsox`, `7=xcity`, `8=dmm`).

### core/ Package Structure

```
core/
  _config/     — AppConfig, config_io, logger, errors, settings_provider
  _models/     — Movie, Actor, ProcessResult dataclasses
  _scraper/    — ScraperBase ABC, ScraperRegistry, ScraperDispatcher, pipeline, adapter, scrapers/
  _services/   — CoreEngine (orchestrator), metadata, naming_service, emby_client
  _files/      — file_utils (getNumber, movie_lists), file_operations (downloads, NFO, moves)
  _media/      — image_processing (watermark, crop, face-detect)
  _net/        — networking (get_html, get_html_javdb, post_html)
  _event/      — EventBus, Event, EventType (pub/sub communication)
```

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

Tests in `core/test/` use pytest, organized into three categories:

| Directory | Purpose |
|-----------|---------|
| `core/test/unit/` | Unit tests (isolated modules) |
| `core/test/integration/` | Integration tests (component interaction) |
| `core/test/live/` | Live scraper tests (require network + video files) |

Key test files:
- `core/test/unit/test_core.py` — Core logic tests (largest file)
- `core/test/unit/test_core_engine.py` — CoreEngine batch/single processing
- `core/test/unit/test_file_ops.py`, `core/test/unit/test_image_ops.py` — File and image operations
- `core/test/unit/test_logger.py`, `core/test/unit/test_config_provider.py` — Infrastructure
- `core/test/unit/test_emby_client.py` — Emby API client
- `core/test/unit/test_scraper_dispatcher.py` — Scraper dispatch logic
- `core/test/unit/test_image_processing.py`, `core/test/unit/test_infrastructure.py` — core/ package
- `core/test/integration/test_event_bus_integration.py` — EventBus integration
- `core/test/live/scrape_test.py`, `core/test/live/test_real_scrape.py` — Live scraper tests
- `core/test/unit/test_errors.py`, `core/test/unit/test_models.py`, `core/test/unit/test_networking.py` — Additional coverage
- `core/test/unit/test_scraper_base.py`, `core/test/unit/test_scraper_adapter.py` — Scraper infrastructure
- `conftest.py` — Shared fixtures: `tmp_dir`, `tmp_log_dir`, `tmp_config_ini`

CLI tests are in `cli/test/` (workspace member).

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

- `docs/requirements.md` — Core I/O contract (what the engine receives and produces), useful when modifying the scrape/organize pipeline.
- `docs/architecture.md` — System architecture overview.
- `docs/scraping-flow.md` — Scraping workflow and pipeline details.

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

### QML Development

QML files live in `pyside6_gui/qml/`. Use `pyside6-qmllint` (shipped with PySide6) for syntax checking:

```bash
.venv/bin/pyside6-qmllint pyside6_gui/qml/             # Lint all QML files
.venv/bin/pyside6-qmllint --ignore unqualified <file>  # Ignore context-property warnings
```

The `unqualified` warning is expected for Python-injected context properties (e.g. `settings.mainMode`). QML filenames must be PascalCase (e.g. `SettingsPage.qml`), and the type name must match exactly.
