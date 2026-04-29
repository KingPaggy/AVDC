import json
import time
from typing import Callable
from core._models.models import Movie
from core._config.errors import ScrapingError

_scraper_cache: dict[str, tuple[str, float]] = {}
_cache_ttl: float = 3600  # 1 hour


def get_cached(key: str, json_str: str, ttl: float = _cache_ttl) -> str | None:
    """Return cached JSON string if still valid, None otherwise."""
    if key in _scraper_cache:
        cached_json, timestamp = _scraper_cache[key]
        if time.time() - timestamp < ttl:
            return cached_json
    return None


def set_cache(key: str, json_str: str) -> None:
    """Store scraper result in cache."""
    _scraper_cache[key] = (json_str, time.time())


def clear_cache() -> None:
    """Clear the scraper cache."""
    _scraper_cache.clear()


def cache_key(source: str, number: str) -> str:
    return f"{source}:{number}"


class ScraperAdapter:
    """Adapter that wraps existing scraper functions with caching."""

    def __init__(self, name: str, func: Callable, priority: int = 100, use_cache: bool = True):
        self.name = name
        self.func = func
        self.priority = priority
        self.use_cache = use_cache

    def __call__(
        self, number: str, appoint_url: str = "", is_uncensored: bool = False
    ) -> str:
        """Return raw JSON string (not parsed). Caching is per-number."""
        key = cache_key(self.name, number)
        if self.use_cache:
            cached = get_cached(key, "")
            if cached is not None:
                return cached

        try:
            result = self.func(number, appoint_url)
            if self.use_cache and isinstance(result, str):
                set_cache(key, result)
            return result
        except Exception as e:
            raise ScrapingError(self.name, number, f"Adapter error: {e}") from e


def create_adapter(name: str, func: Callable, priority: int = 100, use_cache: bool = True) -> ScraperAdapter:
    return ScraperAdapter(name, func, priority, use_cache)
