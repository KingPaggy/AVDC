"""Tests for Function/core_engine.py"""
import os
import tempfile
from unittest.mock import patch, MagicMock, call

import pytest

from Function.config_provider import AppConfig
from Function.core_engine import CoreEngine


def _make_config(**overrides):
    cfg = AppConfig(**overrides)
    return cfg


class TestCoreEngineSingle:
    def test_process_single_timeout(self, tmp_dir):
        """When scraper returns timeout, engine should return 'error'."""
        config = _make_config(media_path=tmp_dir)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)

        with patch("Function.core_engine.getDataFromJSON") as mock_get:
            mock_get.return_value = {"website": "timeout", "title": ""}
            result = engine.process_single(
                filepath=os.path.join(tmp_dir, "test.mp4"),
                number="SSNI-123",
                mode=1,
            )
        assert result == "error"

    def test_process_single_not_found(self, tmp_dir):
        """When scraper returns empty title, engine should return 'not found'."""
        config = _make_config(media_path=tmp_dir)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)

        with patch("Function.core_engine.getDataFromJSON") as mock_get:
            mock_get.return_value = {"website": "", "title": ""}
            result = engine.process_single(
                filepath=os.path.join(tmp_dir, "test.mp4"),
                number="SSNI-123",
                mode=1,
            )
        assert result == "not found"

    def test_process_single_success_scrape_mode(self, tmp_dir):
        """When scraper returns valid data in scrape mode, full pipeline should execute."""
        config = _make_config(media_path=tmp_dir, main_mode=1)
        logs = []
        successes = []
        engine = CoreEngine(config, on_log=logs.append, on_success=successes.append)

        json_response = {
            "title": "Test Title", "number": "SSNI-123", "actor": "Alice",
            "studio": "S1", "publisher": "Will", "year": "2021",
            "outline": "", "runtime": "120", "director": "",
            "release": "2021-05-01", "tag": [], "cover": "http://example.com/cover.jpg",
            "cover_small": "http://example.com/small.jpg", "website": "http://javbus.com",
            "series": "", "actor_photo": {}, "naming_media": "number-title",
            "naming_file": "number", "folder_name": "number",
            "score": "", "imagecut": 1, "extrafanart": [], "source": "javbus",
        }

        with patch("Function.core_engine.getDataFromJSON", return_value=json_response):
            with patch("Function.core_engine.download_thumb"):
                with patch("Function.core_engine.download_small_cover", return_value=None):
                    with patch("Function.core_engine._cut_poster"):
                        with patch("Function.core_engine._fix_image_size"):
                            with patch("Function.core_engine.copy_as_fanart"):
                                with patch("Function.core_engine.delete_thumb"):
                                    with patch("Function.core_engine.paste_file_to_folder", return_value=False):
                                        with patch("Function.core_engine.write_nfo"):
                                            result = engine.process_single(
                                                filepath=os.path.join(tmp_dir, "SSNI-123.mp4"),
                                                number="SSNI-123",
                                                mode=1,
                                            )
        # Should return empty suffix (no cd/cn_sub parts)
        assert result == ""


class TestCoreEngineBatch:
    def test_process_batch_empty(self, tmp_dir):
        """Empty movie list should return zero counts."""
        config = _make_config(media_path=tmp_dir)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)

        with patch("Function.core_engine.movie_lists", return_value=[]):
            result = engine.process_batch(tmp_dir)
        assert result["total"] == 0

    def test_process_batch_single_file(self, tmp_dir):
        """Batch with one file should process it."""
        config = _make_config(media_path=tmp_dir)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)

        filepath = os.path.join(tmp_dir, "SSNI-123.mp4")
        open(filepath, "w").close()

        json_response = {
            "title": "Test", "number": "SSNI-123", "actor": "Alice",
            "studio": "S1", "publisher": "Will", "year": "2021",
            "outline": "", "runtime": "120", "director": "",
            "release": "2021-05-01", "tag": [], "cover": "http://example.com/cover.jpg",
            "cover_small": "", "website": "http://javbus.com",
            "series": "", "actor_photo": {}, "naming_media": "number-title",
            "naming_file": "number", "folder_name": "number",
            "score": "", "imagecut": 1, "extrafanart": [], "source": "javbus",
        }

        with patch("Function.core_engine.movie_lists", return_value=[filepath]):
            with patch("Function.core_engine.getNumber", return_value="SSNI-123"):
                with patch("Function.core_engine.getDataFromJSON", return_value=json_response):
                    with patch("Function.core_engine.download_thumb"):
                        with patch("Function.core_engine.download_small_cover", return_value=None):
                            with patch("Function.core_engine._cut_poster"):
                                with patch("Function.core_engine._fix_image_size"):
                                    with patch("Function.core_engine.copy_as_fanart"):
                                        with patch("Function.core_engine.delete_thumb"):
                                            with patch("Function.core_engine.paste_file_to_folder", return_value=False):
                                                with patch("Function.core_engine.write_nfo"):
                                                    result = engine.process_batch(tmp_dir)
        assert result["total"] == 1
        assert result["success"] == 1
