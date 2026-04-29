# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AVDC (AV Data Capture) is a Python GUI application for scraping JAV website metadata and organizing local video files for Emby/Kodi/Plex. Built with PyQt5, lxml/BeautifulSoup4, requests/cloudscraper, Pillow, and Baidu AIP (face detection).

**Python**: 3.13 (see `.python-version`)

## Common Commands

```bash
uv sync                              # Install dependencies
uv run python AVDC_Main_new.py       # Run the application
uv run python -m pytest test/ -v     # Run tests
uv run python test/scrape_test.py    # Run scraper tests (needs video files)
```

UI Development: Qt Designer `*.ui` files compile to `Ui/AVDC_new.py` via `pyuic5-tool`.

## Architecture

### Layered Structure

The codebase is organized into three layers:

**UI Layer** (`AVDC_Main_new.py`, ~750 lines):
- Pure PyQt5 display and event handling
- Delegates all business logic to `CoreEngine`
- Uses `_get_app_config()` to bridge UI widgets → `AppConfig`

**Business Layer** (`Function/`):
- `core_engine.py` — Main orchestration (`CoreEngine`): batch/single file processing with callback reporting
- `file_ops.py` — File I/O: downloads, NFO generation, file moves, naming
- `image_ops.py` — Image processing: watermark, Baidu AI face crop, poster fix
- `emby_client.py` — Emby API: actor list, profile picture upload
- `config_provider.py` — `AppConfig` dataclass: typed config.ini reader/writer
- `logger.py` — Centralized logging (file + console, no Qt)

**Scraper Layer** (`Function/` + `Getter/`):
- `scraper_base.py` — `ScraperBase` ABC + `ScraperRegistry` + `@register_scraper`
- `scraper_dispatcher.py` — Pattern-based scraper chain selection
- `models.py` — `Movie` dataclass with typed fields
- `scraper_adapter.py` — Legacy `main()` → `Movie` wrapper with caching
- `Function.py` — Legacy dispatch `getDataFromJSON()`, utilities: `getNumber`, `movie_lists`, `check_pic`
- `getHtml.py` — HTTP layer: `get_html()`, `get_html_javdb()`, `post_html()`
- `Getter/*.py` — 7 scrapers: javbus, javdb, jav321, avsox, dmm, mgstage, xcity (each has `main()` + `@register_scraper` subclass)

### Number Pattern Classification

| Pattern | Example | Primary scraper |
|---------|---------|----------------|
| Uncensored | `111111-1111`, `HEYZO-1111`, `n1111` | javbus (uncensored) → javdb → jav321 → avsox |
| FC2 | `FC2-111111`, `FC2-PPV-111111` | javdb |
| Mgstage/amateur | `259LUXU-1111`, `SIRO-1234` | mgstage → jav321 → javdb → javbus |
| DMM style | `ssni00111` (no hyphen/underscore) | dmm |
| European | `sexart.19.11.03` | javdb (US) → javbus (US) |
| Standard censored | `SSIS-123`, `ABP-456` | javbus → jav321 → xcity → javdb → avsox |

### Config

`config.ini` sections: common, proxy, Name_Rule, update, log, media, escape, debug_mode, emby, mark, uncensored, file_download, extrafanart, baidu. **Note**: `[emby] api_key` is sensitive.

### Resources

`Img/` — application icon + watermark overlays (LEAK.png, SUB.png, UNCENSORED.png, 500×300 transparent PNG).

## Adding New Scrapers

1. Subclass `ScraperBase` in `Getter/newsite.py`, implement `scrape()` → `Movie`
2. Apply `@register_scraper` decorator
3. Add entry in `ScraperDispatcher.SCRAPER_MAPPING`

## Proxy Requirements

- DMM requires Japan proxy
- JavDB bans IP after ~30 requests — use proxies or rotate
- `get_html_javdb()` bypasses Cloudflare via cloudscraper
