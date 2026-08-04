"""Tests for jav321 scraper."""
import json
from unittest.mock import patch

from lxml import etree

from core._scraper.scrapers import jav321


class TestJav321FieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        title = jav321.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_actor(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        actors = jav321.getActor(html)
        assert "Actor One" in actors
        assert "Actor Two" in actors

    def test_get_studio(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        studio = jav321.getStudio(html)
        assert "TestStudio" in studio

    def test_get_runtime(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        runtime = jav321.getRuntime(html)
        assert "120" in runtime

    def test_get_series(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        series = jav321.getSeries(html)
        assert "TestSeries" in series

    def test_get_num(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        num = jav321.getNum(html)
        assert "SSIS-123" in num

    def test_get_score(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        score = jav321.getScore(html)
        assert "8.5" in score

    def test_get_release(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        release = jav321.getRelease(html)
        assert "2024-01-15" in release

    def test_get_tag(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        tags = jav321.getTag(html)
        assert isinstance(tags, list)
        assert "Genre1" in tags
        assert "Genre2" in tags

    def test_get_cover(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        detail_page = etree.fromstring(html, etree.HTMLParser())
        cover = jav321.getCover(detail_page)
        assert "ssis00123pl.jpg" in cover

    def test_get_outline(self, load_fixture):
        html = load_fixture("jav321_detail.html")
        detail_page = etree.fromstring(html, etree.HTMLParser())
        outline = jav321.getOutline(detail_page)
        assert "movie outline" in outline


class TestJav321Main:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        detail_html = load_fixture("jav321_detail.html")

        with patch("core._scraper.scrapers.jav321.post_html", return_value=detail_html):
            result = json.loads(jav321.main("SSIS-123", ""))

        assert isinstance(result, dict)
        assert result["title"] != ""
        assert "SSIS-123" in result["number"]
        assert result["source"] == "jav321.py"

    def test_main_handles_not_found(self):
        not_found_html = "<html><body>未找到您要找的AV</body></html>"

        with patch("core._scraper.scrapers.jav321.post_html", return_value=not_found_html):
            result = json.loads(jav321.main("NOTFOUND-999", ""))

        assert result["title"] == ""
        assert result["website"] == ""
