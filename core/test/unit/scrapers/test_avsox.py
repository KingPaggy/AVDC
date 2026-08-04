"""Tests for avsox scraper."""
import json
from unittest.mock import patch


from core._scraper.scrapers import avsox


class TestAvsoxFieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        title = avsox.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_actor(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        actors = avsox.getActor(html)
        assert isinstance(actors, list)
        assert "Actor One" in actors
        assert "Actor Two" in actors

    def test_get_actor_photo(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        actor_photo = avsox.getActorPhoto(html)
        assert isinstance(actor_photo, dict)
        assert "Actor One" in actor_photo
        assert "Actor Two" in actor_photo

    def test_get_studio(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        studio = avsox.getStudio(html)
        assert "Test Studio" in studio

    def test_get_runtime(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        runtime = avsox.getRuntime(html)
        assert "120" in runtime

    def test_get_series(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        series = avsox.getSeries(html)
        assert "Test Series" in series

    def test_get_num(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        num = avsox.getNum(html)
        assert "SSIS-123" in num

    def test_get_release(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        release = avsox.getRelease(html)
        assert "2024-01-15" in release

    def test_get_cover(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        cover = avsox.getCover(html)
        assert "ssis00123pl.jpg" in cover

    def test_get_tag(self, load_fixture):
        html = load_fixture("avsox_detail.html")
        tags = avsox.getTag(html)
        assert isinstance(tags, list)
        assert "Genre1" in tags
        assert "Genre2" in tags


class TestAvsoxSearch:
    """Test search result parsing."""

    def test_get_url_finds_match(self, load_fixture):
        html = load_fixture("avsox_search.html")
        with patch("core._scraper.scrapers.avsox.get_html", return_value=html):
            count, response, url = avsox.getUrl("SSIS-123")
            assert count > 0
            assert "SSIS-123" in url

    def test_get_url_case_insensitive(self, load_fixture):
        html = load_fixture("avsox_search.html")
        with patch("core._scraper.scrapers.avsox.get_html", return_value=html):
            count, response, url = avsox.getUrl("ssis-123")
            assert count > 0


class TestAvsoxMain:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        detail_html = load_fixture("avsox_detail.html")
        search_html = load_fixture("avsox_search.html")

        def mock_get_html(url, cookies=None):
            if "search" in url:
                return search_html
            return detail_html

        with patch("core._scraper.scrapers.avsox.get_html", side_effect=mock_get_html):
            result = json.loads(avsox.main("SSIS-123"))

        assert isinstance(result, dict)
        assert result["title"] != ""
        assert result["number"] != ""
        assert result["source"] == "avsox.website"
