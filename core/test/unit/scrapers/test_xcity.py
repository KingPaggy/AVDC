"""Tests for xcity scraper."""
import json
from unittest.mock import patch


from core._scraper.scrapers import xcity


class TestXcityFieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        title = xcity.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_actor(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        actors = xcity.getActor(html)
        assert "Actor One" in actors
        assert "Actor Two" in actors

    def test_get_actor_photo(self):
        actor_photo = xcity.getActorPhoto("Actor One,Actor Two")
        assert isinstance(actor_photo, dict)
        assert "Actor One" in actor_photo
        assert "Actor Two" in actor_photo

    def test_get_studio(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        studio = xcity.getStudio(html)
        assert "Test Studio" in studio

    def test_get_runtime(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        runtime = xcity.getRuntime(html)
        assert "120" in runtime

    def test_get_series(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        series = xcity.getSeries(html)
        assert "Test Series" in series

    def test_get_num(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        num = xcity.getNum(html)
        assert "SSIS123" in num

    def test_get_release(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        release = xcity.getRelease(html)
        assert "2024-01-15" in release

    def test_get_tag(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        tags = xcity.getTag(html)
        assert "Genre1" in tags
        assert "Genre2" in tags

    def test_get_cover(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        cover = xcity.getCover(html)
        assert "ssis00123pl.jpg" in cover

    def test_get_extrafanart(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        extrafanart = xcity.getExtraFanart(html)
        assert isinstance(extrafanart, list)
        assert len(extrafanart) >= 2

    def test_get_director(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        director = xcity.getDirector(html)
        assert "Test Director" in director

    def test_get_outline(self, load_fixture):
        html = load_fixture("xcity_detail.html")
        outline = xcity.getOutline(html)
        assert "movie outline" in outline


class TestXcitySearch:
    """Test search result parsing."""

    def test_find_number_finds_match(self, load_fixture):
        search_html = load_fixture("xcity_search.html")
        detail_html = load_fixture("xcity_detail.html")

        call_count = [0]
        def mock_get_html(url, cookies=None):
            call_count[0] += 1
            if "result_published" in url:
                return search_html
            return detail_html

        with patch("core._scraper.scrapers.xcity.get_html", side_effect=mock_get_html):
            url, page = xcity.find_number("SSIS-123", "")
            assert url != "not found"
            assert "SSIS123" in page or "SSIS-123" in page


class TestXcityMain:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        search_html = load_fixture("xcity_search.html")
        detail_html = load_fixture("xcity_detail.html")

        def mock_get_html(url, cookies=None):
            if "result_published" in url:
                return search_html
            return detail_html

        with patch("core._scraper.scrapers.xcity.get_html", side_effect=mock_get_html):
            result = json.loads(xcity.main("SSIS-123", ""))

        assert isinstance(result, dict)
        assert result["title"] != ""
        assert result["source"] == "xcity.py"
