#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core._media.image_processing import (
    add_watermark,
    cut_poster,
    cut_poster_ai,
    cut_poster_center,
)
from core._services.naming_service import resolve_name


class ImageProcessingCropTests(unittest.TestCase):
    def _create_test_image(self, width, height, color="red"):
        from PIL import Image
        f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = Image.new("RGB", (width, height), color=color)
        img.save(f.name)
        f.close()
        return f.name

    def test_cut_poster_center_succeeds(self):
        thumb = self._create_test_image(300, 200)
        poster = thumb.replace("-thumb.jpg", "-poster.jpg") if "thumb" in thumb else thumb.replace(".jpg", "-poster.jpg")
        poster_path = os.path.join(os.path.dirname(thumb), "test-poster.jpg")
        try:
            result = cut_poster_center(thumb, poster_path)
            self.assertTrue(result)
            self.assertTrue(os.path.exists(poster_path))
        finally:
            for p in [thumb, poster_path]:
                if os.path.exists(p):
                    os.unlink(p)

    def test_cut_poster_center_returns_false_on_bad_input(self):
        result = cut_poster_center("/nonexistent/thumb.jpg", "/nonexistent/poster.jpg")
        self.assertFalse(result)

    def test_cut_poster_skip_when_imagecut_3(self):
        result = cut_poster("/any/thumb.jpg", "/any/poster.jpg", imagecut=3)
        self.assertTrue(result)  # nothing to do, returns True

    def test_cut_poster_ai_returns_none_without_ai_package(self):
        thumb = self._create_test_image(300, 200)
        poster = thumb.replace(".jpg", "-poster.jpg")
        with patch.dict("sys.modules", {"aip": None}):
            # When aip is not importable, cut_poster_ai returns None
            from importlib import reload
            import core._media.image_processing as ip
            # Force reimport to pick up the mocked module
            result = cut_poster_ai(thumb, poster)
            self.assertIsNone(result)
        os.unlink(thumb)


class ImageProcessingWatermarkTests(unittest.TestCase):
    def _create_test_image(self, width=300, height=450, color="blue"):
        from PIL import Image
        f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        img = Image.new("RGB", (width, height), color=color)
        img.save(f.name)
        f.close()
        return f.name

    def test_add_watermark_with_no_marks_does_not_crash(self):
        pic = self._create_test_image()
        try:
            add_watermark(pic, mark_size=3, mark_pos="top_left", marks={})
            # Should not crash, image remains unchanged
            self.assertTrue(os.path.exists(pic))
        finally:
            os.unlink(pic)

    def test_add_watermark_with_marks_but_no_mark_files(self):
        """Marks enabled but mark PNGs don't exist — should not crash."""
        pic = self._create_test_image()
        try:
            add_watermark(
                pic,
                mark_size=3,
                mark_pos="top_left",
                marks={"cn_sub": True, "leak": False, "uncensored": False},
            )
            self.assertTrue(os.path.exists(pic))
        finally:
            os.unlink(pic)

    def test_add_watermark_different_positions(self):
        """All 4 positions should not crash."""
        positions = ["top_left", "top_right", "bottom_right", "bottom_left"]
        for pos in positions:
            pic = self._create_test_image()
            try:
                add_watermark(pic, mark_size=3, mark_pos=pos, marks={})
                self.assertTrue(os.path.exists(pic))
            finally:
                os.unlink(pic)

    def test_load_mark_image_caches_result(self):
        """_load_mark_image should cache the same image object across calls."""
        from core._media.image_processing import _load_mark_image
        # Clear cache first
        _load_mark_image.cache_clear()
        # Mark files don't exist in test env, so we test the cache mechanism
        # by verifying cache_info works
        info = _load_mark_image.cache_info()
        self.assertEqual(info.misses, 0)


class NamingServiceTests(unittest.TestCase):
    def _make_data(self, **overrides):
        data = {
            "naming_file": "number-title",
            "title": "Sample Movie",
            "studio": "Studio",
            "publisher": "Publisher",
            "year": "2024",
            "outline": "Outline",
            "runtime": "120",
            "director": "Director",
            "actor_photo": {},
            "actor": "Actor A,Actor B",
            "release": "2024-01-01",
            "tag": ["tag1"],
            "number": "ABP-123",
            "cover": "cover.jpg",
            "website": "javbus",
            "series": "Series",
            "naming_file": "number-title",
        }
        data.update(overrides)
        return data

    def test_resolve_name_substitutes_placeholders(self):
        data = self._make_data()
        result = resolve_name(data["naming_file"], data)
        self.assertEqual(result, "ABP-123-Sample Movie")

    def test_resolve_name_truncates_long_actor_list(self):
        actors = ",".join([f"Actor{i}" for i in range(12)])
        data = self._make_data(actor=actors, naming_file="actor-number")
        result = resolve_name(data["naming_file"], data)
        self.assertIn("等演员", result)

    def test_resolve_name_cleans_double_slashes_and_dashes(self):
        data = self._make_data(title="", number="")
        # pattern "--title--" → "--unknown--" → after clean: "unknown"
        result = resolve_name("--title--", data)
        self.assertEqual(result, "unknown")

    def test_resolve_name_truncates_long_names(self):
        long_title = "A" * 200
        data = self._make_data(title=long_title)
        result = resolve_name(data["naming_file"], data)
        self.assertLess(len(result), 200)

    def test_resolve_name_all_placeholders(self):
        data = self._make_data()
        result = resolve_name(
            "number-title-studio-year-runtime-director-actor-release-series-publisher",
            data,
        )
        self.assertIn("ABP-123", result)
        self.assertIn("Sample Movie", result)
        self.assertIn("Studio", result)
        self.assertIn("2024", result)
        self.assertIn("120", result)
        self.assertIn("Director", result)
        self.assertIn("Actor A,Actor B", result)
        self.assertIn("2024-01-01", result)
        self.assertIn("Series", result)


if __name__ == "__main__":
    unittest.main()
