"""Tests for javbus scraper."""
import json
from unittest.mock import patch


from core._scraper.scrapers import javbus


class TestJavbusFieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        title = javbus.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_studio(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        studio = javbus.getStudio(html)
        assert studio == "Test Studio"

    def test_get_publisher(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        publisher = javbus.getPublisher(html)
        assert publisher == "Test Publisher"

    def test_get_year(self):
        assert javbus.getYear("2024-01-15") == "2024"
        assert javbus.getYear("invalid") == "invalid"

    def test_get_release(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        release = javbus.getRelease(html)
        assert "2024-01-15" in release

    def test_get_runtime(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        runtime = javbus.getRuntime(html)
        assert "120" in runtime

    def test_get_actor(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        actors = javbus.getActor(html)
        assert isinstance(actors, list)
        assert "Actor One" in actors
        assert "Actor Two" in actors

    def test_get_num(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        num = javbus.getNum(html)
        assert num == "SSIS-123"

    def test_get_director(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        director = javbus.getDirector(html)
        assert director == "Test Director"

    def test_get_series(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        series = javbus.getSeries(html)
        assert series == "Test Series"

    def test_get_cover(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        cover = javbus.getCover(html)
        assert "ssis00123pl.jpg" in cover

    def test_get_tag(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        tags = javbus.getTag(html)
        assert isinstance(tags, list)
        assert "Genre1" in tags
        assert "Genre2" in tags

    def test_get_extrafanart(self, load_fixture):
        html = load_fixture("javbus_detail.html")
        extrafanart = javbus.getExtraFanart(html)
        assert isinstance(extrafanart, list)
        assert len(extrafanart) == 2


class TestJavbusSearch:
    """Test search result parsing."""

    def test_find_number_finds_match(self, load_fixture):
        html = load_fixture("javbus_search.html")
        with patch("core._scraper.scrapers.javbus.get_html", return_value=html):
            url = javbus.find_number("SSIS-123")
            assert "SSIS-123" in url
            assert url != "not found"

    def test_find_number_case_insensitive(self, load_fixture):
        html = load_fixture("javbus_search.html")
        with patch("core._scraper.scrapers.javbus.get_html", return_value=html):
            url = javbus.find_number("ssis-123")
            assert "SSIS-123" in url


class TestJavbusMain:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        detail_html = load_fixture("javbus_detail.html")
        search_html = load_fixture("javbus_search.html")

        def mock_get_html(url, cookies=None):
            if "search" in url:
                return search_html
            return detail_html

        with patch("core._scraper.scrapers.javbus.get_html", side_effect=mock_get_html):
            with patch("core._scraper.scrapers.javbus.getOutlineScore", return_value=("", "")):
                with patch("core._scraper.scrapers.javbus.getCover_small", return_value=""):
                    result = javbus.main("SSIS-123", "")

        data = json.loads(result)
        assert isinstance(data, dict)
        assert data["title"] != ""
        assert data["number"] == "SSIS-123"
        assert data["studio"] == "Test Studio"
        assert data["release"] != ""
        assert data["source"] == "javbus.py"

    def test_main_handles_not_found(self):
        search_html = "<html><body><div id='waterfall'><div id='waterfall'></div></div></body></html>"

        with patch("core._scraper.scrapers.javbus.get_html", return_value=search_html):
            result = javbus.main("NOTFOUND-999", "")

        data = json.loads(result)
        assert data["title"] == ""
        assert data["website"] == ""
