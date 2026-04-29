"""Tests for core/_scraper/scraper_adapter.py — caching layer and adapter."""
import time
import pytest
from unittest.mock import MagicMock, patch

from core._scraper.scraper_adapter import (
    cache_key, get_cached, set_cache, clear_cache,
    ScraperAdapter, create_adapter,
)
from core._config.errors import ScrapingError


class TestCacheFunctions:
    def setup_method(self):
        clear_cache()

    def test_cache_key_joins_source_and_number(self):
        assert cache_key("javbus", "SSNI-123") == "javbus:SSNI-123"

    def test_set_and_get(self):
        set_cache("test:key", '{"title": "test"}')
        result = get_cached("test:key", "")
        assert result == '{"title": "test"}'

    def test_get_missing_key(self):
        assert get_cached("nonexistent", "") is None

    def test_get_expired_entry(self):
        set_cache("old:key", "old-data")
        far_future = time.time() + 7200
        with patch("core._scraper.scraper_adapter.time.time", return_value=far_future):
            assert get_cached("old:key", "", ttl=3600) is None

    def test_clear_cache(self):
        set_cache("a:1", "data-a")
        set_cache("b:2", "data-b")
        clear_cache()
        assert get_cached("a:1", "") is None
        assert get_cached("b:2", "") is None


class TestScraperAdapter:
    def setup_method(self):
        clear_cache()

    def test_call_invokes_func(self):
        func = MagicMock(return_value='{"title": "ok"}')
        adapter = ScraperAdapter("test", func)
        result = adapter("SSNI-123")
        assert result == '{"title": "ok"}'
        func.assert_called_once_with("SSNI-123", "")

    def test_call_caches_result(self):
        func = MagicMock(return_value='{"title": "ok"}')
        adapter = ScraperAdapter("cached", func)
        adapter("SSNI-123")
        adapter("SSNI-123")  # second call
        assert func.call_count == 1  # cached, not called again

    def test_call_skips_cache_when_disabled(self):
        func = MagicMock(return_value='{"title": "ok"}')
        adapter = ScraperAdapter("nocache", func, use_cache=False)
        adapter("SSNI-123")
        adapter("SSNI-123")  # second call
        assert func.call_count == 2  # not cached

    def test_call_raises_scraping_error_on_exception(self):
        func = MagicMock(side_effect=Exception("network fail"))
        adapter = ScraperAdapter("bad", func)
        with pytest.raises(ScrapingError, match="Adapter error: network fail"):
            adapter("SSNI-123")

    def test_priority_default(self):
        adapter = ScraperAdapter("default", lambda n, u: "{}")
        assert adapter.priority == 100

    def test_custom_priority(self):
        adapter = ScraperAdapter("high", lambda n, u: "{}", priority=5)
        assert adapter.priority == 5


class TestCreateAdapter:
    def test_creates_adapter_with_defaults(self):
        func = lambda n, u: "{}"
        adapter = create_adapter("factory", func)
        assert adapter.name == "factory"
        assert adapter.func is func
        assert adapter.priority == 100
        assert adapter.use_cache is True

    def test_creates_adapter_with_overrides(self):
        func = lambda n, u: "{}"
        adapter = create_adapter("custom", func, priority=1, use_cache=False)
        assert adapter.priority == 1
        assert adapter.use_cache is False
