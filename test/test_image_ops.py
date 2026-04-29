"""Tests for Function/image_ops.py"""
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from PIL import Image

from core.config import AppConfig
from core.image_processing import (
    crop_by_face_detection,
    cut_poster_from_thumb as cut_poster,
    fix_image_size,
    apply_marks,
    _add_watermark_overlay,
)


def _create_test_image(path, width=200, height=300, color=(255, 0, 0)):
    """Create a simple solid-color test image."""
    img = Image.new("RGB", (width, height), color)
    img.save(path)


class TestCutPoster:
    def test_crops_right_half(self, tmp_dir):
        """imagecut != 3 and != 0 should crop the right half of thumb."""
        thumb = os.path.join(tmp_dir, "test-thumb.jpg")
        _create_test_image(thumb, width=300, height=450)
        # imagecut=1 → crop right half
        cut_poster(imagecut=1, path=tmp_dir, naming_rule="test", baidu_credentials=None)
        poster = os.path.join(tmp_dir, "test-poster.jpg")
        assert os.path.exists(poster)
        with Image.open(poster) as img:
            # Should be roughly 300-300/1.9 = ~142 wide, full height
            assert img.width < 300
            assert img.height == 450

    def test_skips_when_exists(self, tmp_dir):
        """Should not overwrite existing poster."""
        thumb = os.path.join(tmp_dir, "test-thumb.jpg")
        poster = os.path.join(tmp_dir, "test-poster.jpg")
        _create_test_image(thumb, 300, 450)
        _create_test_image(poster, 100, 150)
        mtime = os.path.getmtime(poster)
        cut_poster(imagecut=1, path=tmp_dir, naming_rule="test", baidu_credentials=None)
        assert os.path.getmtime(poster) == mtime  # not modified

    def test_skips_imagecut_3(self, tmp_dir):
        """imagecut==3 is handled by small_cover_download, not here."""
        cut_poster(imagecut=3, path=tmp_dir, naming_rule="test", baidu_credentials=None)
        assert not os.path.exists(os.path.join(tmp_dir, "test-poster.jpg"))

    def test_calls_baidu_when_imagecut_0(self, tmp_dir):
        """imagecut==0 should call Baidu body analysis."""
        thumb = os.path.join(tmp_dir, "test-thumb.jpg")
        _create_test_image(thumb, 300, 450)

        # Mock Baidu AipBodyAnalysis to avoid network calls
        mock_result = {
            "person_info": [{
                "body_parts": {"nose": {"x": 100}}
            }]
        }
        with patch("aip.AipBodyAnalysis") as MockClient:
            mock_instance = MockClient.return_value
            mock_instance.bodyAnalysis.return_value = mock_result
            cut_poster(
                imagecut=0, path=tmp_dir, naming_rule="test",
                baidu_credentials={"app_id": "1", "api_key": "2", "secret_key": "3"},
            )
        MockClient.assert_called_once_with("1", "2", "3")
        mock_instance.bodyAnalysis.assert_called_once()
        poster = os.path.join(tmp_dir, "test-poster.jpg")
        assert os.path.exists(poster)


class TestFixImageSize:
    def test_fixes_wrong_aspect_ratio(self, tmp_dir):
        """If poster ratio is not ~2:3, it should be padded."""
        poster = os.path.join(tmp_dir, "test-poster.jpg")
        # Create a square image (1:1 ratio, not 2:3)
        _create_test_image(poster, 300, 300)
        fix_image_size(tmp_dir, "test")
        with Image.open(poster) as img:
            w, h = img.size
            ratio = w / h
            assert 2 / 3 - 0.05 <= ratio <= 2 / 3 + 0.05

    def test_skips_correct_aspect_ratio(self, tmp_dir):
        """Poster with ~2:3 ratio should not be modified."""
        poster = os.path.join(tmp_dir, "test-poster.jpg")
        _create_test_image(poster, 200, 300)  # exactly 2:3
        fix_image_size(tmp_dir, "test")
        with Image.open(poster) as img:
            assert img.size == (200, 300)


class TestApplyMarks:
    def test_no_marks_when_all_false(self, tmp_dir):
        """If cn_sub=leak=uncensored=0, no marks should be applied."""
        pic = os.path.join(tmp_dir, "test.jpg")
        _create_test_image(pic, 500, 750)
        with Image.open(pic) as before:
            data_before = list(before.tobytes())
        apply_marks(pic, 0, 0, 0, {"mark_size": 10, "mark_pos": "top_left"})
        with Image.open(pic) as after:
            data_after = list(after.tobytes())
        assert data_before == data_after

    def test_marks_when_watermark_files_missing(self, tmp_dir):
        """If watermark files don't exist, apply_marks should not crash."""
        pic = os.path.join(tmp_dir, "test.jpg")
        _create_test_image(pic, 500, 750)
        apply_marks(pic, 1, 0, 0, {"mark_size": 10, "mark_pos": "top_left"})
        # Should not raise
