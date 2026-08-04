"""Tests for mgstage scraper."""
import json
from unittest.mock import patch


from core._scraper.scrapers import mgstage


class TestMgstageFieldExtraction:
    """Test individual field extraction functions."""

    def test_get_title(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        title = mgstage.getTitle(html)
        assert "SSIS-123" in title
        assert "Test Movie Title" in title

    def test_get_actor(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        actors = mgstage.getActor(html)
        assert "ActorOne" in actors
        assert "ActorTwo" in actors

    def test_get_actor_photo(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        actors = mgstage.getActor(html).split(",")
        actor_photo = mgstage.getActorPhoto(actors)
        assert isinstance(actor_photo, dict)
        assert "ActorOne" in actor_photo

    def test_get_studio(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        studio = mgstage.getStudio(html)
        assert "TestStudio" in studio

    def test_get_publisher(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        publisher = mgstage.getPublisher(html)
        assert "TestLabel" in publisher

    def test_get_runtime(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        runtime = mgstage.getRuntime(html)
        assert "120" in runtime

    def test_get_series(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        series = mgstage.getSeries(html)
        assert "TestSeries" in series

    def test_get_num(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        num = mgstage.getNum(html)
        assert "SSIS-123" in num

    def test_get_release(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        release = mgstage.getRelease(html)
        assert "2024-01-15" in release

    def test_get_tag(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        tags = mgstage.getTag(html)
        assert "Genre1" in tags
        assert "Genre2" in tags

    def test_get_cover(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        cover = mgstage.getCover(html)
        assert "ssis00123pl.jpg" in cover

    def test_get_extrafanart(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        extrafanart = mgstage.getExtraFanart(html)
        assert isinstance(extrafanart, list)
        assert len(extrafanart) >= 2

    def test_get_outline(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        outline = mgstage.getOutline(html)
        assert "movie outline" in outline

    def test_get_score(self, load_fixture):
        html = load_fixture("mgstage_detail.html")
        score = mgstage.getScore(html)
        assert "8.5" in score


class TestMgstageMain:
    """Test main() function with mocked network."""

    def test_main_returns_complete_dict(self, load_fixture):
        detail_html = load_fixture("mgstage_detail.html")

        with patch("core._scraper.scrapers.mgstage.get_html", return_value=detail_html):
            result = json.loads(mgstage.main("SSIS-123", ""))

        assert isinstance(result, dict)
        assert result["title"] != ""
        assert result["number"] != ""
        assert result["source"] == "mgstage.py"
