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
  config.py               #   AppConfig dataclass
  logger.py               #   Centralized logging
  orchestrator.py         #   CoreEngine — batch/single processing
  file_operations.py      #   Downloads, NFO, file moves
  file_utils.py           #   Number extraction, path utilities
  image_processing.py     #   Watermark, face-detect crop, poster fix
  emby_client.py          #   Emby API client
  metadata.py             #   JSON field normalization
  naming_service.py       #   Naming rule resolution
  networking.py           #   HTTP with proxy/retry
  models.py               #   Movie, Actor, ScraperResult dataclasses
  scraper_base.py         #   ScraperBase ABC + Registry
  scraper_dispatcher.py   #   Pattern-based scraper chain selection
  scrape_pipeline.py      #   Scrape orchestration with caching
  scraper_adapter.py      #   Legacy adapter + cache
  event_bus.py            #   Pub/sub communication
  events.py               #   Event types
  settings_provider.py    #   Config abstraction layer
  errors.py               #   Typed exceptions
  process_result.py       #   ProcessResult dataclass
  config_io.py            #   ConfigParser I/O
  scrapers/               #   7 scraper implementations
    avsox.py, dmm.py, jav321.py, javbus.py, javdb.py, mgstage.py, xcity.py
resources/                # Static assets
  icons/                  #   App icons (AVDC-ico.png, AVDC.ico)
  watermarks/             #   Watermark overlays (SUB.png, LEAK.png, UNCENSORED.png)
  screenshots/            #   README images
Ui/                       # Compiled PyQt5 UI from Qt Designer
docs/                     # Documentation
test/                     # Test suite

### CoreEngine (`core/orchestrator.py`)

The main orchestrator for the scrape/organize workflow. Qt-free — accepts `AppConfig` and reports via callbacks (`on_log`, `on_progress`, `on_success`, `on_failure`). Two entry points:

- `process_batch(movie_path, escape_folder, mode)` — scan directory, process all files
- `process_single(filepath, number, mode, appoint_url)` — single file

### core/ Package (Public API)

Defined in `core/__init__.py` — all core functionality accessible via `from core import ...`:

- **Config**: `get_config()` → `AppConfig` dataclass, `get_default_config()`, `get_proxy_config()` via `core.config_io`
- **Data models**: `Movie`, `Actor`, `ScraperResult` dataclasses in `core/models.py`
- **Scraper infrastructure**: `ScraperBase` ABC, `ScraperRegistry`, `@register_scraper`, `ScraperDispatcher` (pattern-based chain), `ScraperAdapter` (legacy wrapper with caching)
- **Scrape pipeline**: `getDataFromJSON()` in `core/scrape_pipeline.py`
- **File utilities**: `getNumber()`, `is_uncensored()`, `movie_lists()`, `escapePath()`, `check_pic()` in `core/file_utils.py`
- **Image processing**: `add_watermark()`, `cut_poster()`, `cut_poster_ai()` in `core/image_processing.py`
- **Naming**: `resolve_name()` in `core/naming_service.py`
- **Networking**: `get_html()`, `get_html_javdb()`, `post_html()`, `get_proxies()` in `core/networking.py`
- **Event system**: `EventBus` (thread-safe pub/sub), `Event`, `EventType` enum — all UI↔core communication flows through typed events. Usage: `bus.on(EventType.LOG_INFO, handler)` / `bus.emit(EventType.LOG_INFO, message="hello")`
- **Settings interface**: `SettingsProvider` ABC in `core/settings_provider.py` — core queries runtime config through this abstraction instead of reaching into UI widgets
- **Process results**: `ProcessResult` dataclass + `ProcessStatus` enum in `core/process_result.py`
- **Errors**: `AVDCError`, `ConfigError`, `ScrapingError`, `NetworkError`, `ImageError`, `FileError` in `core/errors.py`

### Scraper Layer (`core/scrapers/`)

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

Tests in `test/` use pytest. Key test files:
- `test_core.py` — Core logic tests (largest file)
- `test_core_engine.py` — CoreEngine batch/single processing
- `test_file_ops.py`, `test_image_ops.py` — File and image operations
- `test_logger.py`, `test_config_provider.py` — Infrastructure
- `test_emby_client.py` — Emby API client
- `test_scraper_dispatcher.py` — Scraper dispatch logic
- `test_image_processing.py`, `test_infrastructure.py` — core/ package
- `test_event_bus_integration.py` — EventBus integration
- `scrape_test.py`, `test_real_scrape.py` — Live scraper tests (require video files)
- `conftest.py` — Shared fixtures: `tmp_dir`, `tmp_log_dir`, `tmp_config_ini`

### Proxy Requirements

- DMM requires Japan proxy
- JavDB bans IP after ~30 requests — use proxies or rotate
- `get_html_javdb()` bypasses Cloudflare via cloudscraper
- Proxy config in `config.ini [proxy]` section

### Adding New Scrapers

1. Create `core/scrapers/newsite.py`, subclass `ScraperBase`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `core/scraper_dispatcher.py` `SCRAPER_MAPPING`
4. Add import in `core/scrape_pipeline.py` `get_scraper_modules()`

## Config

`config.ini` sections: common, proxy, Name_Rule, update, log, media, escape, debug_mode, emby, mark, uncensored, file_download, extrafanart, baidu. **Note**: `[emby] api_key` is sensitive.

## Reference Documents

- `docs/requirements.md` — Core I/O contract (what the engine receives and produces), useful when modifying the scrape/organize pipeline.

## Entry Points

- `AVDC_Main_new.py` — PyQt5 GUI entry
- `cli.py` — Standalone CLI (no Qt dependency): `uv run python cli.py --path /path/to/movies`
