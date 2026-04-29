# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**IMPORTANT: Do NOT create git worktrees. Always work directly in the project root directory (`/Users/pageking/Development/09-AVDC_Page/`).**

## Project Overview

AVDC (AV Data Capture) is a Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex. Built with PyQt5, lxml/BeautifulSoup4, requests/cloudscraper, Pillow, and Baidu AIP (face detection).

**Python**: 3.13 (see `.python-version`)

## Common Commands

```bash
uv sync                              # Install dependencies
uv run python AVDC_Main_new.py       # Run the application
uv run python -m pytest test/ -v     # Run all tests
uv run python -m pytest test/test_core_engine.py -v  # Single test file
```

UI Development: Qt Designer `*.ui` files compile to `Ui/AVDC_new.py` via `pyuic5-tool`.

## Architecture

### Package Layout

```
AVDC_Main_new.py          # UI layer: PyQt5 display + event handling
cli.py                    # Standalone CLI (no Qt dependency)
core/                     # ALL business logic (typed, no Qt)
  __init__.py             #   Package docstring only
  _config/                #   AppConfig, logging, errors, settings
  _models/                #   Movie, Actor, ProcessResult
  _scraper/               #   Base, dispatcher, adapter, pipeline
  _services/              #   CoreEngine, metadata, naming, emby_client
  _files/                 #   file_utils, file_operations
  _media/                 #   image_processing
  _net/                   #   networking
  _event/                 #   EventBus, events
  scrapers/               #   7 scraper implementations
    avsox.py, dmm.py, jav321.py, javbus.py, javdb.py, mgstage.py, xcity.py
resources/                # Static assets
  icons/                  #   App icons (AVDC-ico.png, AVDC.ico)
  watermarks/             #   Watermark overlays (SUB.png, LEAK.png, UNCENSORED.png)
  screenshots/            #   README images
Ui/                       # Compiled PyQt5 UI from Qt Designer
docs/                     # Documentation
test/                     # Test suite

### CoreEngine (`core/_services/orchestrator.py`)

The main orchestrator for the scrape/organize workflow. Qt-free — accepts `AppConfig` and reports via callbacks (`on_log`, `on_progress`, `on_success`, `on_failure`). Two entry points:

- `process_batch(movie_path, escape_folder, mode)` — scan directory, process all files
- `process_single(filepath, number, mode, appoint_url)` — single file

### core/ Package Structure

```
core/
  _config/     — AppConfig, config_io, logger, errors, settings_provider
  _models/     — Movie, Actor, ProcessResult dataclasses
  _scraper/    — ScraperBase ABC, ScraperRegistry, ScraperDispatcher, pipeline, adapter
  _services/   — CoreEngine (orchestrator), metadata, naming_service, emby_client
  _files/      — file_utils (getNumber, movie_lists), file_operations (downloads, NFO, moves)
  _media/      — image_processing (watermark, crop, face-detect)
  _net/        — networking (get_html, get_html_javdb, post_html)
  _event/      — EventBus, Event, EventType (pub/sub communication)
  scrapers/    — avsox, dmm, jav321, javbus, javdb, mgstage, xcity
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

### Scraper Layer (`core/_scraper/` + `core/scrapers/`)

Infrastructure in `core/_scraper/` (base, dispatcher, adapter, pipeline).
Site implementations in `core/scrapers/` (avsox, dmm, jav321, javbus, javdb, mgstage, xcity).

Seven scraper modules, each with `main()` + `@register_scraper` subclass:

| Scraper | File | Notes |
|---------|------|-------|
| javbus | `core/scrapers/javbus.py` | Primary for censored; also handles uncensored |
| javdb | `core/scrapers/javdb.py` | Primary for FC2; uses cloudscraper for CF bypass |
| jav321 | `core/scrapers/jav321.py` | Fallback |
| avsox | `core/scrapers/avsox.py` | Fallback |
| dmm | `core/scrapers/dmm.py` | Requires Japan proxy |
| mgstage | `core/scrapers/mgstage.py` | Primary for mgstage/amateur patterns |
| xcity | `core/scrapers/xcity.py` | Fallback |

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

Tests in `test/` use pytest, organized into three categories:

| Directory | Purpose |
|-----------|---------|
| `test/unit/` | Unit tests (isolated modules) |
| `test/integration/` | Integration tests (component interaction) |
| `test/live/` | Live scraper tests (require network + video files) |

Key test files:
- `test/unit/test_core.py` — Core logic tests (largest file)
- `test/unit/test_core_engine.py` — CoreEngine batch/single processing
- `test/unit/test_file_ops.py`, `test/unit/test_image_ops.py` — File and image operations
- `test/unit/test_logger.py`, `test/unit/test_config_provider.py` — Infrastructure
- `test/unit/test_emby_client.py` — Emby API client
- `test/unit/test_scraper_dispatcher.py` — Scraper dispatch logic
- `test/unit/test_image_processing.py`, `test/unit/test_infrastructure.py` — core/ package
- `test/integration/test_event_bus_integration.py` — EventBus integration
- `test/live/scrape_test.py`, `test/live/test_real_scrape.py` — Live scraper tests
- `test/unit/test_cli.py` — CLI argument parsing
- `test/unit/test_errors.py`, `test/unit/test_models.py`, `test/unit/test_networking.py` — Additional coverage
- `test/unit/test_scraper_base.py`, `test/unit/test_scraper_adapter.py` — Scraper infrastructure
- `conftest.py` — Shared fixtures: `tmp_dir`, `tmp_log_dir`, `tmp_config_ini`

### Proxy Requirements

- DMM requires Japan proxy
- JavDB bans IP after ~30 requests — use proxies or rotate
- `get_html_javdb()` bypasses Cloudflare via cloudscraper
- Proxy config in `config.ini [proxy]` section

### Adding New Scrapers

1. Create `core/scrapers/newsite.py`, subclass `ScraperBase`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `core/_scraper/scraper_dispatcher.py` `SCRAPER_MAPPING`
4. Add import in `core/_scraper/scrape_pipeline.py` `get_scraper_modules()`

## Config

`config.ini` sections: common, proxy, Name_Rule, update, log, media, escape, debug_mode, emby, mark, uncensored, file_download, extrafanart, baidu. **Note**: `[emby] api_key` is sensitive.

## Reference Documents

- `docs/requirements.md` — Core I/O contract (what the engine receives and produces), useful when modifying the scrape/organize pipeline.

## Entry Points

- `AVDC_Main_new.py` — PyQt5 GUI entry
- `cli.py` — Standalone CLI (no Qt dependency): `uv run python cli.py --path /path/to/movies`
