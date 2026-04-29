"""Tests for Function/core_engine.py"""
import os
import tempfile
from unittest.mock import patch, MagicMock, call

import pytest

from core._config.config import AppConfig
from core._services.orchestrator import CoreEngine


def _make_config(**overrides):
    cfg = AppConfig(**overrides)
    return cfg


class TestCoreEngineSingle:
    def test_process_single_timeout(self, tmp_dir):
        """When scraper returns timeout, engine should return 'error'."""
        config = _make_config(media_path=tmp_dir)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)

        with patch("core._services.orchestrator.getDataFromJSON") as mock_get:
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

        with patch("core._services.orchestrator.getDataFromJSON") as mock_get:
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

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with patch("core._services.orchestrator.download_thumb"):
                with patch("core._services.orchestrator.download_small_cover", return_value=None):
                    with patch("core._services.orchestrator._cut_poster"):
                        with patch("core._services.orchestrator._fix_image_size"):
                            with patch("core._services.orchestrator.copy_as_fanart"):
                                with patch("core._services.orchestrator.delete_thumb"):
                                    with patch("core._services.orchestrator.paste_file_to_folder", return_value=False):
                                        with patch("core._services.orchestrator.write_nfo"):
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

        with patch("core._services.orchestrator.movie_lists", return_value=[]):
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

        with patch("core._services.orchestrator.movie_lists", return_value=[filepath]):
            with patch("core._services.orchestrator.getNumber", return_value="SSNI-123"):
                with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
                    with patch("core._services.orchestrator.download_thumb"):
                        with patch("core._services.orchestrator.download_small_cover", return_value=None):
                            with patch("core._services.orchestrator._cut_poster"):
                                with patch("core._services.orchestrator._fix_image_size"):
                                    with patch("core._services.orchestrator.copy_as_fanart"):
                                        with patch("core._services.orchestrator.delete_thumb"):
                                            with patch("core._services.orchestrator.paste_file_to_folder", return_value=False):
                                                with patch("core._services.orchestrator.write_nfo"):
                                                    result = engine.process_batch(tmp_dir)
        assert result["total"] == 1
        assert result["success"] == 1


# ========================================================================
# Process single core — branch tests
# ========================================================================


class TestProcessSingleCoreBranches:
    """Test edge-case branches in _process_single_core."""

    def test_cover_url_missing_raises_exception(self, tmp_dir):
        """When scraper returns data without cover URL, engine raises."""
        config = _make_config(media_path=tmp_dir)
        engine = CoreEngine(config)
        json_response = {
            "title": "Test", "number": "SSNI-123", "website": "javbus",
            "cover": "local_file.jpg",  # no "http" prefix
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with pytest.raises(Exception, match="Cover Url"):
                engine._process_single_core(
                    filepath=os.path.join(tmp_dir, "test.mp4"),
                    number="SSNI-123", mode=1, count=1,
                    success_folder=os.path.join(tmp_dir, "out"),
                    failed_folder=os.path.join(tmp_dir, "fail"),
                )

    def test_cover_small_missing_when_imagecut_3_raises(self, tmp_dir):
        """imagecut=3 with no cover_small URL raises."""
        config = _make_config(media_path=tmp_dir)
        engine = CoreEngine(config)
        json_response = {
            "title": "Test", "number": "SSNI-123", "website": "javbus",
            "cover": "http://example.com/cover.jpg",
            "cover_small": "", "imagecut": 3,
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with pytest.raises(Exception, match="Cover_small Url"):
                engine._process_single_core(
                    filepath=os.path.join(tmp_dir, "test.mp4"),
                    number="SSNI-123", mode=1, count=1,
                    success_folder=os.path.join(tmp_dir, "out"),
                    failed_folder=os.path.join(tmp_dir, "fail"),
                )

    def test_organize_mode_skips_downloads(self, tmp_dir):
        """main_mode=2 (organize) should skip download/watermark pipeline."""
        config = _make_config(media_path=tmp_dir, main_mode=2)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)
        json_response = {
            "title": "Organized Movie", "number": "ORG-001",
            "website": "javbus", "cover": "http://example.com/c.jpg",
            "cover_small": "", "imagecut": 1,
            "series": "", "actor_photo": {}, "extrafanart": [],
            "naming_media": "number", "naming_file": "number",
            "folder_name": "number", "actor": "", "tag": [],
            "score": "", "studio": "", "publisher": "", "year": "",
            "outline": "", "runtime": "", "director": "", "release": "",
            "source": "",
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with patch("core._services.orchestrator.create_output_folder", return_value=tmp_dir):
                with patch("core._services.orchestrator.paste_file_to_folder", return_value=False) as mock_paste:
                    result = engine._process_single_core(
                        filepath=os.path.join(tmp_dir, "ORG-001.mp4"),
                        number="ORG-001", mode=1, count=1,
                        success_folder=os.path.join(tmp_dir, "out"),
                        failed_folder=os.path.join(tmp_dir, "fail"),
                    )
        # In organize mode, only paste_file is called
        mock_paste.assert_called_once()
        # No download_thumb, no cut_poster, no watermarks
        assert result == ""

    def test_leak_detection_adds_suffix(self, tmp_dir):
        """File with '流出' in name should add suffix."""
        config = _make_config(media_path=tmp_dir)
        engine = CoreEngine(config)
        json_response = {
            "title": "Leak Movie", "number": "LEAK-001",
            "website": "javbus", "cover": "http://example.com/c.jpg",
            "imagecut": 1, "cover_small": "",
            "series": "", "actor_photo": {}, "extrafanart": [],
            "naming_media": "number", "naming_file": "number",
            "folder_name": "number", "actor": "", "tag": [],
            "score": "", "studio": "", "publisher": "", "year": "",
            "outline": "", "runtime": "", "director": "", "release": "",
            "source": "",
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with patch("core._services.orchestrator.create_output_folder", return_value=os.path.join(tmp_dir, "out")):
                with patch("core._services.orchestrator.download_thumb"):
                    with patch("core._services.orchestrator.paste_file_to_folder", return_value=False):
                        result = engine._process_single_core(
                            filepath=os.path.join(tmp_dir, "流出-LEAK-001.mp4"),
                            number="LEAK-001", mode=1, count=1,
                            success_folder=tmp_dir,
                            failed_folder=os.path.join(tmp_dir, "fail"),
                        )
        assert result == ""  # no cd/sub suffix

    def test_multi_part_detection_adds_cd_suffix(self, tmp_dir):
        """File with -CD1 should include disc part in suffix."""
        config = _make_config(media_path=tmp_dir)
        engine = CoreEngine(config)
        json_response = {
            "title": "Multi", "number": "MULTI-001",
            "website": "javbus", "cover": "http://example.com/c.jpg",
            "imagecut": 1, "cover_small": "",
            "series": "", "actor_photo": {}, "extrafanart": [],
            "naming_media": "number", "naming_file": "number",
            "folder_name": "number", "actor": "", "tag": [],
            "score": "", "studio": "", "publisher": "", "year": "",
            "outline": "", "runtime": "", "director": "", "release": "",
            "source": "",
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with patch("core._services.orchestrator.create_output_folder", return_value=os.path.join(tmp_dir, "out")):
                with patch("core._services.orchestrator.download_thumb"):
                    with patch("core._services.orchestrator.paste_file_to_folder", return_value=False):
                        with patch("core._services.orchestrator.copy_as_fanart"):
                            with patch("core._services.orchestrator.delete_thumb"):
                                result = engine._process_single_core(
                                    filepath=os.path.join(tmp_dir, "MULTI-001-CD1.mp4"),
                                    number="MULTI-001", mode=1, count=1,
                                    success_folder=tmp_dir,
                                    failed_folder=os.path.join(tmp_dir, "fail"),
                                )
        assert "-CD1" in result

    def test_chinese_subtitle_detection(self, tmp_dir):
        """File with '-C.' or '字幕' should add -C suffix."""
        config = _make_config(media_path=tmp_dir)
        engine = CoreEngine(config)
        json_response = {
            "title": "Sub", "number": "SUB-001",
            "website": "javbus", "cover": "http://example.com/c.jpg",
            "imagecut": 1, "cover_small": "",
            "series": "", "actor_photo": {}, "extrafanart": [],
            "naming_media": "number", "naming_file": "number",
            "folder_name": "number", "actor": "", "tag": [],
            "score": "", "studio": "", "publisher": "", "year": "",
            "outline": "", "runtime": "", "director": "", "release": "",
            "source": "",
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with patch("core._services.orchestrator.create_output_folder", return_value=os.path.join(tmp_dir, "out")):
                with patch("core._services.orchestrator.download_thumb"):
                    with patch("core._services.orchestrator.paste_file_to_folder", return_value=False):
                        with patch("core._services.orchestrator.copy_as_fanart"):
                            with patch("core._services.orchestrator.delete_thumb"):
                                result = engine._process_single_core(
                                    filepath=os.path.join(tmp_dir, "SUB-001-C.mp4"),
                                    number="SUB-001", mode=1, count=1,
                                    success_folder=tmp_dir,
                                    failed_folder=os.path.join(tmp_dir, "fail"),
                                )
        assert "-C" in result

    def test_uncensored_poster_override(self, tmp_dir):
        """uncensored_poster=1 with imagecut=3 should set imagecut to 0."""
        config = _make_config(media_path=tmp_dir, uncensored_poster=1)
        logs = []
        engine = CoreEngine(config, on_log=logs.append)
        json_response = {
            "title": "Uncensored", "number": "UNC-001",
            "website": "javbus", "cover": "http://example.com/c.jpg",
            "cover_small": "http://example.com/small.jpg",
            "imagecut": 3,  # will be overridden to 0
            "series": "", "actor_photo": {}, "extrafanart": [],
            "naming_media": "number", "naming_file": "number",
            "folder_name": "number", "actor": "", "tag": [],
            "score": "", "studio": "", "publisher": "", "year": "",
            "outline": "", "runtime": "", "director": "", "release": "",
            "source": "",
        }

        with patch("core._services.orchestrator.getDataFromJSON", return_value=json_response):
            with patch("core._services.orchestrator.create_output_folder", return_value=os.path.join(tmp_dir, "out")):
                with patch("core._services.orchestrator.download_thumb"):
                    with patch("core._services.orchestrator.download_small_cover", return_value=None):
                        with patch("core._services.orchestrator._cut_poster") as mock_cut:
                            with patch("core._services.orchestrator._fix_image_size"):
                                with patch("core._services.orchestrator.copy_as_fanart"):
                                    with patch("core._services.orchestrator.delete_thumb"):
                                        with patch("core._services.orchestrator.paste_file_to_folder", return_value=False):
                                            engine._process_single_core(
                                                filepath=os.path.join(tmp_dir, "UNC-001.mp4"),
                                                number="UNC-001", mode=1, count=1,
                                                success_folder=tmp_dir,
                                                failed_folder=os.path.join(tmp_dir, "fail"),
                                            )
        # imagecut should be 0 after override → cut_poster called with imagecut=0
        mock_cut.assert_called_once()
        assert mock_cut.call_args[0][0] == 0  # first arg is imagecut

    def test_batch_failed_file_counted(self, tmp_dir):
        """Batch should correctly count failed files."""
        config = _make_config(media_path=tmp_dir)
        engine = CoreEngine(config)

        with patch("core._services.orchestrator.movie_lists", return_value=[os.path.join(tmp_dir, "fail.mp4")]):
            with patch("core._services.orchestrator.getNumber", return_value=""):
                result = engine.process_batch(tmp_dir)
        assert result["total"] == 1
        assert result["success"] == 0
        assert result["failed"] == 1
