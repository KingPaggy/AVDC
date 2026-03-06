import json
import functools
from typing import Optional, Callable
from Function.models import Movie


class ScraperAdapter(Callable):
    """Adapter that wraps existing scraper functions to return Movie objects."""

    def __init__(self, name: str, func: Callable, priority: int = 100):
        self.name = name
        self.func = func
        self.priority = priority

    def __call__(
        self, number: str, appoint_url: str = "", is_uncensored: bool = False
    ) -> Movie:
        try:
            result = self.func(number, appoint_url)
            if isinstance(result, str):
                data = json.loads(result)
            elif isinstance(result, dict):
                data = result
            else:
                return Movie.empty()

            return Movie.from_dict(data)
        except Exception as e:
            print(f"Error in {self.name} adapter: {e}")
            return Movie.empty()

    def scrape(
        self, number: str, appoint_url: str = "", is_uncensored: bool = False
    ) -> Movie:
        return self(number, appoint_url, is_uncensored)


def create_adapter(name: str, func: Callable, priority: int = 100) -> ScraperAdapter:
    return ScraperAdapter(name, func, priority)


_scraper_cache: dict[str, tuple[Movie, float]] = {}
_cache_ttl: float = 3600


def get_cached(key: str, func: Callable[[], Movie], ttl: float = _cache_ttl) -> Movie:
    """Cache scraper results to avoid repeated requests."""
    import time

    if key in _scraper_cache:
        movie, timestamp = _scraper_cache[key]
        if time.time() - timestamp < ttl:
            return movie

    movie = func()
    import time

    _scraper_cache[key] = (movie, time.time())
    return movie


def clear_cache() -> None:
    """Clear the scraper cache."""
    _scraper_cache.clear()


def cache_key(source: str, number: str) -> str:
    return f"{source}:{number}"
