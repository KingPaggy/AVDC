# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AVDC (AV Data Capture) is a Python-based GUI application for scraping metadata from Japanese adult video (JAV) websites and organizing local video files for integration with media servers like Emby, Kodi, and Plex.

**Key Technologies**: Python 3.8+, PyQt5, lxml/BeautifulSoup4 (HTML parsing), requests/cloudscraper (HTTP with Cloudflare bypass), Pillow (image processing), Baidu AI (image recognition)

## Common Commands

### Development Setup
```bash
# Install dependencies using pip
pip install -r py-require.txt

# Or use uv (modern Python package manager)
uv sync

# Run the main application
python AVDC_Main_new.py
```

### UI Development
- Qt Designer files (`*.ui`) are compiled to Python using `pyuic5-tool`
- Compiled UI is in `Ui/AVDC_new.py`

### Configuration
- Main configuration file: `config.ini` (must be in the same directory as the executable)
- Log files are saved to the `Log/` directory when `save_log = 1`

## Architecture Overview

### Layer Structure
```
AVDC_Page/
├── AVDC_Main_new.py    # Main application entry point (UI + business logic combined)
├── Ui/
│   └── AVDC_new.py     # Compiled PyQt5 UI layout
├── Function/
│   ├── Function.py     # Core dispatch logic, file operations, utilities
│   └── getHtml.py      # HTTP request handling with proxy/retry support
└── Getter/
    ├── javbus.py       # Scraper for javbus.com
    ├── javdb.py        # Scraper for javdb.com
    ├── jav321.py       # Scraper for jav321.com
    ├── avsox.py        # Scraper for avsox.com
    ├── dmm.py          # Scraper for dmm.co.jp (requires Japan proxy)
    ├── mgstage.py      # Scraper for mgstage.com
    └── xcity.py        # Scraper for xcity.jp
```

### Key Components

**Scraper Architecture** (Getter modules):
- Each scraper has a `main(number, appoint_url, isuncensored=False)` function
- Returns JSON string with metadata fields: title, actor, studio, publisher, outline, score, runtime, director, release, number, cover, extrafanart, tag, series, year, actor_photo, website, source
- Cloudflare bypass is handled via `cloudscraper` (used in `get_html_javdb()`)
- DMM requires a Japan proxy to work properly

**Dispatch Logic** (`Function/Function.py`):
- `getDataFromJSON(file_number, config, mode, appoint_url)`: Main scraper dispatcher
- `mode` parameter determines which scrapers to try:
  - `1`: All scrapers (default)
  - `2`: mgstage only
  - `3`: javbus only
  - `4`: jav321 only
  - `5`: javdb only
  - `6`: avsox only
  - `7`: xcity only
  - `8`: dmm only
- Scrapers are tried sequentially; the first successful result is used

**Number Pattern Detection**:
- Uncensored: `^\d{4,}` (e.g., `111111-1111`), `n\d{4}`, `HEYZO-*`, and custom prefixes from config
- FC2: `FC2-\d{5,}`
- European: `\D+\.\d{2}\.\d{2}\.\d{2}` (e.g., `sexart.19.11.03`)
- Standard censored: `SSIS-123`, `ABP-456`
- Mixed: `259LUXU-1111` (mgstage)

**HTTP Handling** (`Function/getHtml.py`):
- `get_html(url, cookies)`: Standard GET with proxy support and retry
- `get_html_javdb(url)`: Uses cloudscraper for Cloudflare bypass
- `post_html(url, query)`: POST request support
- Proxy settings read from `config.ini` [proxy] section

## Important File Patterns

### Number Naming Conventions (Critical for Scraping)
- Standard censored: `SSNI-111`, `IPX-123`, `ABP-456`
- Uncensored: `111111-1111`, `111111_1111`, `HEYZO-1111`, `n1111`
- FC2: `FC2-111111`, `FC2-PPV-111111`
- Mgstage/amateur: `259LUXU-1111`, `SIRO-1234`
- European: `sexart.19.11.03` (series.year.month.day)

### File Naming Supports
- Multi-disc: `ssni-xxx-cd1.mp4`, `ssni-xxx-cd2.mp4`
- With subtitles: `ssni-xxx-c.mp4`, `ssni-xxx-C.mp4`
- Combined: `abp-xxx-CD1-C.mp4` (disc first, subtitle last)

## Configuration System (config.ini)

### Sections
- `[common]`: main_mode, output folders, website selection, soft_link mode
- `[proxy]`: type (no/http/socks5), proxy address, timeout, retry count
- `[Name_Rule]`: folder_name, naming_media, naming_file patterns
- `[media]`: media_type extensions, sub_type extensions, media_path
- `[escape]`: literals, folders, strings to exclude
- `[debug_mode]`: switch for debug output
- `[emby]`: emby_url, api_key for actor photo upload
- `[mark]`: watermark settings (poster_mark, thumb_mark, mark_size, mark_type, mark_pos)
- `[uncensored]`: uncensored_prefix, uncensored_poster (0=official, 1=cut)
- `[file_download]`: nfo, poster, fanart, thumb download toggles
- `[extrafanart]`: extrafanart_download, extrafanart_folder

## Known Issues and Architecture Notes

**Current Architecture Limitations** (from `dev-log/修改意见.md`):
- `AVDC_Main_new.py` is a "god class" mixing UI, business logic, and file operations
- No unified interface for scrapers (all return JSON dict but no contract)
- Hard-coded scraper dispatch logic in `Function.py` - adding new sites requires modifying multiple files
- Data flows as raw dicts instead of typed classes, making maintenance difficult
- UI and logic are tightly coupled

**Proxy Requirements**:
- DMM requires a Japan proxy to access content
- JavDB may ban IP after ~30 requests - use proxies or switch sites
- Cloudflare protection is handled via `cloudscraper` library

## Adding New Scraper Sites

To add a new scraping website:

1. Create a new file in `Getter/` directory (e.g., `newsite.py`)
2. Implement a `main(number, appoint_url, isuncensored=False)` function that returns JSON
3. Import it in `Function/Function.py`
4. Add dispatch logic in `getDataFromJSON()` function
5. Update `config.ini` website option comments and UI dropdown in `AVDC_Main_new.py`

## Number Extraction Logic (`getNumber()`)

The `getNumber()` function in `Function/Function.py` handles complex pattern matching to extract video numbers from filenames. It processes:
- Removes escape strings from config
- Extracts `-CDn` or `-cdn` for multi-disc (removes from main number)
- Handles date patterns `\d{4}-\d{1,2}-\d{1,2}`
- Supports multiple hyphen/underscore formats

## File Processing Workflow

1. `movie_lists()` scans directory for video files matching extensions
2. For each file: `getNumber()` extracts the video ID
3. `getDataFromJSON()` dispatches to appropriate scrapers based on number pattern
4. If successful: download metadata, rename/move to output directory
5. If failed (and `failed_file_move = 1`): move to failed directory

## Testing Scraper Changes

When modifying scrapers:
- Test with real number examples from each supported site
- Verify JSON output has all required fields
- Check Cloudflare bypass still works (for javdb)
- Test with both censored and uncensored content
- Verify image URLs are properly formed

## ⚠️ 开发流程强制要求

以下规则必须在每次代码变更时严格遵守：

### 1. 单次功能提交原则

**每完成一个功能点实现，必须立即提交一次 Git commit。** 禁止将多个无关功能合并到一次提交中。每次提交应包含完整的功能实现和对应的测试。

### 2. 开发日志强制要求

**每次代码提交前，必须更新 `dev-log/CHANGELOG.md` 文件。** 该文件是项目的唯一开发记录来源，必须包含以下两部分：

#### 2.1 本次提交详细说明（每次提交添加在文件顶部）

格式如下：

```markdown
## [YYYY-MM-DD HH:MM:SS] - {提交摘要标题}

- **提交哈希**: {git commit hash 前 7 位}
- **涉及文件**:
  - `path/to/file1.py` — 变更说明
  - `path/to/file2.py` — 变更说明
- **详细说明**:
  - 本次提交解决了什么问题
  - 新增/修改了哪些功能
  - 是否有破坏性变更
  - 测试结果
```

#### 2.2 项目总结（每次提交追加到文件底部）

以 bullet list 形式存在，每一项的开头必须是时间戳，后接简要功能介绍和相关文件。格式如下：

```markdown
## 项目总结

- **2026-04-28 14:30** — 添加了事件总线基础设施，新增 `core/events.py`、`core/event_bus.py`，定义 17 种事件类型和线程安全的 EventBus 实现
- **2026-04-28 15:00** — Service 层适配 EventBus，修改 `application/file_processing_service.py` 接受 `bus=` 和 `settings=` 参数
```

### 3. 执行顺序

1. 实现功能
2. 编写/运行测试，确保通过
3. 更新 `dev-log/CHANGELOG.md`（添加本次提交详细说明 + 更新项目总结）
4. 提交 Git commit（commit message 应简明扼要描述变更）
5. 重复步骤 1-4 直到所有功能完成

### 4. CHANGELOG.md 模板

如果文件不存在，使用以下模板创建：

```markdown
# 开发日志

> 本项目的所有开发记录，包括提交详情和项目总结。

---

<!-- 本次提交详细说明 — 新的提交添加在此处上方 -->

---

## 项目总结

<!-- 项目总结 — bullet list 格式，每次提交追加一项 -->
```
