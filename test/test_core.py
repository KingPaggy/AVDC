#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
from configparser import ConfigParser
from pathlib import Path

from core.config_io import get_config, get_config_file, save_config
from core.file_utils import escapePath, getNumber, getDataState, is_uncensored, movie_lists
from core.metadata import get_info


class CoreFileUtilsTests(unittest.TestCase):
    def test_get_number_standard_formats(self):
        cases = {
            "SSIS-123.mp4": "SSIS-123",
            "259LUXU-1111.mkv": "259LUXU-1111",
            "FC2-PPV-123456.mp4": "FC2-123456",
            "sexart.19.11.03.mp4": "sexart.19.11.03",
            "ABC123.mp4": "ABC-123",
            "SIVR-123-CD1.mp4": "SIVR-123",
        }

        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(getNumber(filename, ""), expected)

    def test_movie_lists_filters_hidden_and_excluded_folders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "keep").mkdir()
            (root / "failed").mkdir()
            (root / "keep" / "a.mp4").write_text("x", encoding="utf-8")
            (root / "keep" / ".hidden.mp4").write_text("x", encoding="utf-8")
            (root / "failed" / "b.mp4").write_text("x", encoding="utf-8")

            result = movie_lists("failed", ".mp4|.mkv", str(root))
            self.assertEqual(result, [str(root / "keep" / "a.mp4")].copy())

    def test_escape_path_removes_escaped_literals(self):
        config = ConfigParser()
        config.read_dict({"escape": {"literals": ":|?"}})

        self.assertEqual(
            escapePath(r"C:\foo\:bar\?baz", config),
            r"C:\foobarbaz",
        )

    def test_is_uncensored_uses_config_prefixes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                Path("config.ini").write_text(
                    "[uncensored]\nuncensored_prefix = ABC|XYZ\n",
                    encoding="utf-8",
                )
                self.assertTrue(is_uncensored("XYZ-1234"))
                self.assertFalse(is_uncensored("ABP-123"))
            finally:
                os.chdir(cwd)

    def test_get_data_state(self):
        self.assertEqual(getDataState({"title": ""}), 0)
        self.assertEqual(getDataState({"title": "None"}), 0)
        self.assertEqual(getDataState({"title": "null"}), 0)
        self.assertEqual(getDataState({"title": "Movie"}), 1)


class CoreConfigTests(unittest.TestCase):
    def test_get_config_and_save_config_roundtrip(self):
        payload = {
            "main_mode": 1,
            "failed_output_folder": "failed",
            "success_output_folder": "output",
            "failed_file_move": 1,
            "soft_link": 0,
            "show_poster": 1,
            "website": "all",
            "type": "no",
            "proxy": "127.0.0.1:7890",
            "timeout": 30,
            "retry": 3,
            "folder_name": "title",
            "naming_media": "number",
            "naming_file": "number",
            "update_check": 0,
            "save_log": 1,
            "media_type": ".mp4|.mkv",
            "sub_type": ".srt",
            "media_path": ".",
            "literals": ":|?",
            "folders": "failed",
            "string": "",
            "switch_debug": 0,
            "emby_url": "",
            "api_key": "",
            "poster_mark": 0,
            "thumb_mark": 0,
            "mark_size": 1,
            "mark_type": "sub",
            "mark_pos": "bottom_right",
            "uncensored_prefix": "ABC|XYZ",
            "uncensored_poster": 0,
            "nfo_download": 1,
            "poster_download": 1,
            "fanart_download": 1,
            "thumb_download": 1,
            "extrafanart_download": 0,
            "extrafanart_folder": "extrafanart",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                save_config(payload)
                self.assertTrue(Path("config.ini").exists())

                config = get_config()
                self.assertEqual(config.get("common", "website"), "all")
                self.assertEqual(config.get("proxy", "proxy"), "127.0.0.1:7890")
                self.assertEqual(config.get("uncensored", "uncensored_prefix"), "ABC|XYZ")
                self.assertEqual(get_config_file(), "config.ini")
            finally:
                os.chdir(cwd)


class CoreMetadataTests(unittest.TestCase):
    def test_get_info_normalizes_empty_fields(self):
        data = {
            "title": "Movie",
            "studio": "",
            "publisher": "N/A",
            "year": "2024",
            "outline": "",
            "runtime": "120",
            "director": "",
            "actor_photo": {},
            "actor": "Actor",
            "release": "2024-01-01",
            "tag": [],
            "number": "ABP-123",
            "cover": "cover.jpg",
            "website": "javbus",
            "series": "",
        }

        result = get_info(data)
        self.assertEqual(result[0], "Movie")
        self.assertEqual(result[1], "unknown")
        self.assertEqual(result[2], "unknown")
        self.assertEqual(result[14], "unknown")


if __name__ == "__main__":
    unittest.main()
