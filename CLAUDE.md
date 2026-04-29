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

The codebase is undergoing a layered refactoring from a monolithic UI structure into three packages:

```
AVDC_Main_new.py          # UI layer: PyQt5 display + event handling
application/              # High-level app services (batch, file system, remote)
core/                     # Business logic: typed models, scraper infra, networking
Function/                 # Legacy business layer (being migrated into core/)
Getter/                   # Scraper implementations (7 sites)
Ui/                       # Compiled PyQt5 UI from Qt Designer
```

### Refactoring Status

The legacy `Function/` layer has been partially decomposed into `core/` and `application/` packages. Migration is progressing; during the transition, `Function/` modules still handle orchestration and heavy lifting.

| Package | Purpose | Status |
|---------|---------|--------|
| `core/` | Typed business logic with event-driven API | Active |
| `application/` | Higher-level services composing core | Active |
| `Function/` | Legacy modules (core_engine, config_provider, file_ops, image_ops, emby_client, logger) | Shrinking |
| `AVDC_Main_new.py` | PyQt5 UI | Needs decoupling |

### CoreEngine (`Function/core_engine.py`)

The main orchestrator for the scrape/organize workflow. Qt-free — accepts `AppConfig` and reports via callbacks (`on_log`, `on_progress`, `on_success`, `on_failure`). Two entry points:

- `process_batch(movie_path, escape_folder, mode)` — scan directory, process all files
- `process_single(filepath, number, mode, appoint_url)` — single file

### Legacy `Function/` Modules

| Module | Purpose |
|--------|---------|
| `config_provider.py` | `AppConfig` dataclass — typed relay between config.ini and business logic |
| `core_engine.py` | Orchestrator (see above) |
| `file_ops.py` | Downloads, NFO generation, file moves, naming — all Qt-free |
| `image_ops.py` | Watermarking, Baidu AI face-detect cropping, size fixing |
| `logger.py` | Centralized logging (backed by file), UI reads via QTimer polling |
| `emby_client.py` | Emby API client for actor/profile photo upload |
| `getHtml.py` | HTTP helpers with proxy/retry (migrating into `core/networking.py`) |

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

### application/ Package

- `batch_service.py` — Batch processing orchestration
- `file_processing_service.py` — Single/multi file metadata + media processing
- `file_system_service.py` — File watching, scanning, organizing
- `remote_service.py` — Remote storage/external integration

### Scraper Layer (Getter/)

Seven scraper modules in `Getter/`, each with `main()` + `@register_scraper` subclass:

| Scraper | File | Notes |
|---------|------|-------|
| javbus | `javbus.py` | Primary for censored; also handles uncensored |
| javdb | `javdb.py` | Primary for FC2; uses cloudscraper for CF bypass |
| jav321 | `jav321.py` | Fallback |
| avsox | `avsox.py` | Fallback |
| dmm | `dmm.py` | Requires Japan proxy |
| mgstage | `mgstage.py` | Primary for mgstage/amateur patterns |
| xcity | `xcity.py` | Fallback |

All scrapers are discovered automatically via `ScraperRegistry` + `@register_scraper` decorator, then dispatched by `ScraperDispatcher` based on number pattern matching.

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
- `test_core.py` — Core logic tests (largest file, ~56k)
- `test_core_engine.py`, `test_file_ops.py`, `test_image_ops.py`, `test_logger.py`, `test_emby_client.py` — Function/ module tests
- `test_config_provider.py`, `test_scraper_dispatcher.py` — Legacy module tests
- `test_file_processing_service.py`, `test_file_system_service.py`, `test_batch_service.py` — application/ service tests
- `test_image_processing.py`, `test_infrastructure.py`, `test_event_bus_integration.py` — core/ package tests
- `test_remote_service.py` — Remote service tests
- `scrape_test.py`, `test_real_scrape.py` — Live scraper tests (require video files)
- `conftest.py` — Shared fixtures: `tmp_dir`, `tmp_log_dir`, `tmp_config_ini`

Run a single test file: `uv run python -m pytest test/test_core.py -v`

### Proxy Requirements

- DMM requires Japan proxy
- JavDB bans IP after ~30 requests — use proxies or rotate
- `get_html_javdb()` bypasses Cloudflare via cloudscraper
- Proxy config in `config.ini [proxy]` section

### Adding New Scrapers

1. Subclass `ScraperBase` in `Getter/newsite.py`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `ScraperDispatcher.SCRAPER_MAPPING`

## Config

`config.ini` sections: common, proxy, Name_Rule, update, log, media, escape, debug_mode, emby, mark, uncensored, file_download, extrafanart, baidu. **Note**: `[emby] api_key` is sensitive.

## Resources

`Img/` — application icon + watermark overlays (LEAK.png, SUB.png, UNCENSORED.png, 500×300 transparent PNG).

## Reference Documents

- `docs/requirements.md` — Core I/O contract (what the engine receives and produces), useful when modifying the scrape/organize pipeline.
- `main.py` — Stub entry point (placeholder for future CLI). The real application entry is `AVDC_Main_new.py`.

## Refactoring Conventions

- `_trash/` — Archive directory for files removed during refactoring (preserves history without git deletion).
