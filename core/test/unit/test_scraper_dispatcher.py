"""Tests for ScraperBase, ScraperRegistry, and ScraperDispatcher integration."""
import json
from unittest.mock import patch

import pytest

from core._scraper.scraper_base import ScraperBase, register_scraper, ScraperRegistry
from core._models.models import Movie


class TestMovie:
    def test_from_dict_basic(self):
        data = {
            "title": "Test", "number": "SSNI-123", "actor": "Alice,Bob",
            "studio": "S1", "publisher": "Will", "year": "2021",
            "outline": "Outline", "runtime": "120", "director": "Tanaka",
            "release": "2021-05-01", "tag": ["tag1"], "cover": "http://c.jpg",
            "website": "http://x.com", "series": "Series", "actor_photo": {},
            "naming_media": "", "naming_file": "", "folder_name": "",
            "cover_small": "", "score": "8.5", "imagecut": 1,
            "extrafanart": [], "source": "javbus",
        }
        movie = Movie.from_dict(data)
        assert movie.title == "Test"
        assert movie.number == "SSNI-123"
        assert movie.actor == ["Alice", "Bob"]
        assert movie.tag == ["tag1"]
        assert movie.runtime == 120

    def test_is_valid(self):
        assert Movie(title="Test").is_valid()
        assert not Movie(title="").is_valid()
        assert not Movie(title="None").is_valid()
        assert not Movie(title="null").is_valid()

    def test_to_dict_roundtrip(self):
        m1 = Movie(title="Test", number="SSNI-123", actor=["Alice"])
        data = m1.to_dict()
        m2 = Movie.from_dict(data)
        assert m2.title == m1.title
        assert m2.number == m1.number
        assert m2.actor == m1.actor

    def test_empty(self):
        m = Movie.empty()
        assert not m.is_valid()


class TestScraperRegistry:
    def setup_method(self):
        ScraperRegistry.clear()

    def test_register_and_get(self):
        @register_scraper
        class TestScraper(ScraperBase):
            name = "test"
            priority = 100

            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        scraper = ScraperRegistry.get_by_name("test")
        assert scraper is not None
        assert scraper.name == "test"

    def test_priority_sorting(self):
        @register_scraper
        class Low(ScraperBase):
            name = "low"
            priority = 999

            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        @register_scraper
        class High(ScraperBase):
            name = "high"
            priority = 1

            def scrape(self, number, appoint_url="", is_uncensored=False):
                return Movie.empty()

        sorted_list = ScraperRegistry.get_scrapers()
        assert sorted_list[0].name == "high"
        assert sorted_list[1].name == "low"


class TestScraperDispatcher:
    """Test the dispatcher without importing existing Getter modules."""

    def test_uncensored_detection(self):
        from core._scraper.scraper_dispatcher import ScraperDispatcher
        assert ScraperDispatcher.is_uncensored("111111-1111")
        assert ScraperDispatcher.is_uncensored("HEYZO-1234")
        assert ScraperDispatcher.is_uncensored("n1234")
        assert not ScraperDispatcher.is_uncensored("SSNI-123")

    def test_fc2_detection(self):
        from core._scraper.scraper_dispatcher import ScraperDispatcher
        assert ScraperDispatcher.is_fc2("FC2-123456")
        assert not ScraperDispatcher.is_fc2("SSNI-123")

    def test_get_auto_chain_standard(self):
        from core._scraper.scraper_dispatcher import ScraperDispatcher
        chain = ScraperDispatcher.get_scraper_chain("SSNI-123", mode=1)
        # Standard chain should start with javbus
        assert "javbus.main" in chain[0][0]

    def test_get_auto_chain_fc2(self):
        from core._scraper.scraper_dispatcher import ScraperDispatcher
        chain = ScraperDispatcher.get_scraper_chain("FC2-123456", mode=1)
        assert len(chain) == 1
        assert "javdb" in chain[0][0]

    def test_get_auto_chain_uncensored(self):
        from core._scraper.scraper_dispatcher import ScraperDispatcher
        chain = ScraperDispatcher.get_scraper_chain("111111-1111", mode=1)
        assert "javbus.main_uncensored" in chain[0][0]

    def test_single_site_modes(self):
        from core._scraper.scraper_dispatcher import ScraperDispatcher
        assert ScraperDispatcher.get_scraper_chain("SSNI-123", mode=2) == [("mgstage.main", 5)]
        assert ScraperDispatcher.get_scraper_chain("SSNI-123", mode=6) == [("avsox.main", 50)]
        assert ScraperDispatcher.get_scraper_chain("SSNI-123", mode=8) == [("dmm.main", 70)]
