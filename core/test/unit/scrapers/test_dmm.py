"""Tests for dmm scraper."""
import json
from unittest.mock import patch


from core._scraper.scrapers import dmm


class TestDmmFieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        title = dmm.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_actor(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        actors = dmm.getActor(html)
        assert "Actor One" in actors
        assert "Actor Two" in actors

    def test_get_studio(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        studio = dmm.getStudio(html)
        assert "Test Studio" in studio

    def test_get_runtime(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        runtime = dmm.getRuntime(html)
        assert "120" in runtime

    def test_get_label(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        label = dmm.getLabel(html)
        assert "Test Label" in label

    def test_get_num(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        num = dmm.getNum(html)
        assert "SSIS-123" in num

    def test_get_release(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        release = dmm.getRelease(html)
        assert "2024-01-15" in release

    def test_get_tag(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        tags = dmm.getTag(html)
        assert isinstance(tags, list)
        assert "Genre1" in tags
        assert "Genre2" in tags

    def test_get_director(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        director = dmm.getDirector(html)
        assert "Test Director" in director

    def test_get_outline(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        outline = dmm.getOutline(html)
        assert "movie outline" in outline

    def test_get_series(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        series = dmm.getSeries(html)
        assert "Test Series" in series

    def test_get_score(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        score = dmm.getScore(html)
        assert "8.5" in score

    def test_get_publisher(self, load_fixture):
        html = load_fixture("dmm_detail.html")
        publisher = dmm.getPublisher(html)
        assert "Test Label" in publisher


class TestDmmMain:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        detail_html = load_fixture("dmm_detail.html")

        with patch("core._scraper.scrapers.dmm.get_html", return_value=detail_html):
            result = json.loads(dmm.main("SSIS-123"))

        assert isinstance(result, dict)
        assert result["title"] != ""
        assert result["source"] == "fanza.py"

    def test_main_handles_404(self):
        with patch("core._scraper.scrapers.dmm.get_html", return_value="404 Not Found"):
            result = json.loads(dmm.main("NOTFOUND-999"))
            assert result["title"] == ""
            assert result["website"] == ""
