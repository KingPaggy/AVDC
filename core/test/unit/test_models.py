"""Tests for core/_models/models.py — Actor, Movie, ScraperResult."""
import pytest
from core._models.models import Actor, Movie, ScraperResult


class TestActor:
    def test_actor_name_only(self):
        a = Actor(name="楓ふうあ")
        assert a.name == "楓ふうあ"
        assert a.photo is None

    def test_actor_with_photo(self):
        a = Actor(name="三上悠亜", photo="http://example.com/pic.jpg")
        assert a.name == "三上悠亜"
        assert a.photo == "http://example.com/pic.jpg"


class TestMovieEdgeCases:
    def test_from_dict_actor_as_list(self):
        data = {"title": "Test", "actor": ["Alice", "Bob"]}
        m = Movie.from_dict(data)
        assert m.actor == ["Alice", "Bob"]

    def test_from_dict_actor_as_string(self):
        data = {"title": "Test", "actor": "Alice,Bob"}
        m = Movie.from_dict(data)
        assert m.actor == ["Alice", "Bob"]

    def test_from_dict_tag_as_list(self):
        data = {"title": "Test", "tag": ["big", "small"]}
        m = Movie.from_dict(data)
        assert m.tag == ["big", "small"]

    def test_from_dict_tag_as_string(self):
        data = {"title": "Test", "tag": "big,small"}
        m = Movie.from_dict(data)
        assert m.tag == ["big", "small"]

    def test_from_dict_runtime_as_int(self):
        data = {"title": "Test", "runtime": 120}
        m = Movie.from_dict(data)
        assert m.runtime == 120

    def test_from_dict_runtime_as_string_digits(self):
        data = {"title": "Test", "runtime": "120"}
        m = Movie.from_dict(data)
        assert m.runtime == 120

    def test_from_dict_runtime_as_string_non_digit(self):
        data = {"title": "Test", "runtime": "N/A"}
        m = Movie.from_dict(data)
        assert m.runtime == 0

    def test_empty_movie(self):
        m = Movie.empty()
        assert m.title == ""
        assert m.actor == []
        assert not m.is_valid()

    def test_is_valid_with_none_title(self):
        m = Movie(title="None")
        assert not m.is_valid()

    def test_is_valid_with_null_title(self):
        m = Movie(title="null")
        assert not m.is_valid()

    def test_to_dict_converts_runtime(self):
        m = Movie(title="Test", number="ABC-123", runtime=120)
        d = m.to_dict()
        assert d["runtime"] == "120"

    def test_to_dict_empty_runtime(self):
        m = Movie(title="Test", runtime=0)
        d = m.to_dict()
        assert d["runtime"] == ""

    def test_to_dict_roundtrip(self):
        original = Movie.from_dict({
            "title": "Test", "number": "ABC-123", "actor": ["Alice"],
            "studio": "S1", "runtime": "120", "tag": ["big"],
            "cover": "http://c.jpg", "extrafanart": ["http://f1.jpg"],
            "score": "8.0", "imagecut": 1,
        })
        data = original.to_dict()
        restored = Movie.from_dict(data)
        assert restored.title == original.title
        assert restored.number == original.number
        assert restored.actor == original.actor
        assert restored.runtime == original.runtime
        assert restored.tag == original.tag


class TestScraperResult:
    def test_success_result(self):
        movie = Movie(title="Test")
        result = ScraperResult(movie=movie, source="javbus", success=True)
        assert result.movie.title == "Test"
        assert result.source == "javbus"
        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        movie = Movie.empty()
        result = ScraperResult(movie=movie, source="javdb", success=False, error="timeout")
        assert result.success is False
        assert result.error == "timeout"
