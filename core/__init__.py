"""Core application services for AVDC.

These modules contain reusable logic that should stay independent from the UI
layer so that the application can later swap PyQt5 for PySide6/QML without
rewriting business rules.

Public API:
    from core import get_config, getNumber, is_uncensored, movie_lists
    from core import Movie, Actor, ScraperResult
    from core import resolve_name, get_info, check_pic
    from core import add_watermark, cut_poster, cut_poster_ai
    from core import getDataFromJSON
    from core import get_default_config, get_proxy_config
"""

# Config
from core.config_io import get_config, get_default_config, get_proxy_config

# File utilities
from core.file_utils import (
    getNumber,
    is_uncensored,
    movie_lists,
    escapePath,
    getDataState,
    check_pic,
)

# Metadata
from core.metadata import get_info

# Naming
from core.naming_service import resolve_name

# Image processing
from core.image_processing import add_watermark, cut_poster, cut_poster_ai

# Networking
from core.networking import get_html, get_html_javdb, post_html, get_proxies

# Scraper pipeline
from core.scrape_pipeline import getDataFromJSON

# Data models
from core.models import Movie, Actor, ScraperResult

# Scraper infrastructure
from core.scraper_base import ScraperBase, ScraperRegistry, register_scraper
from core.scraper_adapter import ScraperAdapter, cache_key, get_cached, clear_cache
from core.scraper_dispatcher import ScraperDispatcher
