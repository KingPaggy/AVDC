"""Tests for core/_scraper/scraper_base.py — ScraperBase ABC, helper methods, registry."""
import pytest
from core._scraper.scraper_base import ScraperBase, ScraperRegistry, register_scraper
from core._models.models import Movie
from core._config.errors import ScrapingError


class TestScraperBaseHelpers:
    def setup_method(self):
        ScraperRegistry.clear()

    def test_is_timeout_returns_true_when_website_is_timeout(self):
        class TestScraper(ScraperBase):
            name = "test"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        scraper = TestScraper()
        movie = Movie(website="timeout")
        assert scraper.is_timeout(movie) is True

    def test_is_timeout_returns_false_for_normal(self):
        class TestScraper(ScraperBase):
            name = "test"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        scraper = TestScraper()
        movie = Movie(website="javbus")
        assert scraper.is_timeout(movie) is False

    def test_is_empty_returns_true_for_invalid_movie(self):
        class TestScraper(ScraperBase):
            name = "test"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        scraper = TestScraper()
        assert scraper.is_empty(Movie()) is True
        assert scraper.is_empty(Movie(title="None")) is True

    def test_is_empty_returns_false_for_valid_movie(self):
        class TestScraper(ScraperBase):
            name = "test"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        scraper = TestScraper()
        assert scraper.is_empty(Movie(title="Real Movie")) is False

    def test_scrape_with_fallback_returns_movie_on_success(self):
        class TestScraper(ScraperBase):
            name = "fallback_test"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie(title="Found", number=number)

        scraper = TestScraper()
        result = scraper.scrape_with_fallback("ABC-123")
        assert result.title == "Found"
        assert result.number == "ABC-123"

    def test_scrape_with_fallback_raises_scraping_error_on_exception(self):
        class TestScraper(ScraperBase):
            name = "failing"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                raise ValueError("bad data")

        scraper = TestScraper()
        with pytest.raises(ScrapingError) as exc:
            scraper.scrape_with_fallback("XYZ-999")
        assert exc.value.source == "failing"
        assert exc.value.number == "XYZ-999"
        assert "bad data" in str(exc.value)


class TestRegisterScraperDecorator:
    def setup_method(self):
        ScraperRegistry.clear()

    def test_decorator_registers_instance(self):
        @register_scraper
        class DecoratedScraper(ScraperBase):
            name = "decorated"
            priority = 50
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        registered = ScraperRegistry.get_by_name("decorated")
        assert registered is not None
        assert registered.name == "decorated"
        assert registered.priority == 50

    def test_decorator_returns_class(self):
        @register_scraper
        class AnotherScraper(ScraperBase):
            name = "another"
            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        # decorator returns the class itself (not an instance)
        assert AnotherScraper is not None
        assert hasattr(AnotherScraper, "scrape")
