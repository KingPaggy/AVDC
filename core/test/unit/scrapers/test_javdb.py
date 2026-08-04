"""Tests for javdb scraper."""
import json
from unittest.mock import patch


from core._scraper.scrapers import javdb


class TestJavdbFieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        title = javdb.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_actor(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        actors = javdb.getActor(html)
        assert "Actor One" in actors
        assert "Actor Two" in actors

    def test_get_studio(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        studio = javdb.getStudio(html)
        assert "Test Studio" in studio

    def test_get_publisher(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        publisher = javdb.getPublisher(html)
        assert "Test Publisher" in publisher

    def test_get_runtime(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        runtime = javdb.getRuntime(html)
        assert "120" in runtime

    def test_get_series(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        series = javdb.getSeries(html)
        assert "Test Series" in series

    def test_get_number(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        number = javdb.getNumber(html)
        assert "SSIS-123" in number

    def test_get_release(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        release = javdb.getRelease(html)
        assert "2024-01-15" in release

    def test_get_tag(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        tags = javdb.getTag(html)
        assert "Genre1" in tags
        assert "Genre2" in tags

    def test_get_cover(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        cover = javdb.getCover(html)
        assert "ssis00123pl.jpg" in cover

    def test_get_extrafanart(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        extrafanart = javdb.getExtraFanart(html)
        assert isinstance(extrafanart, list)
        assert len(extrafanart) >= 2

    def test_get_director(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        director = javdb.getDirector(html)
        assert "Test Director" in director

    def test_get_score(self, load_fixture):
        html = load_fixture("javdb_detail.html")
        score = javdb.getScore(html)
        assert "8.5" in score


class TestJavdbMain:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        detail_html = load_fixture("javdb_detail.html")
        search_html = load_fixture("javdb_search.html")

        def mock_get_html_javdb(url):
            if "search" in url:
                return search_html
            return detail_html

        with patch("core._scraper.scrapers.javdb.get_html_javdb", side_effect=mock_get_html_javdb):
            with patch("core._scraper.scrapers.javdb.getOutlineScore", return_value=("", "")):
                result = javdb.main("SSIS-123", "")

        result = json.loads(result)
        assert isinstance(result, dict)
        assert result["title"] != ""
        assert "SSIS-123" in result["number"]
        assert result["source"] == "javdb.py"
