#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import tempfile
import unittest
from configparser import ConfigParser
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.config_io import get_config, get_config_file, save_config
from core.file_utils import escapePath, getNumber, getDataState, is_uncensored, movie_lists
from core.metadata import get_info
import core.scrape_pipeline as scrape_pipeline


class CoreFileUtilsTests(unittest.TestCase):
    def test_get_number_standard_formats(self):
        cases = {
            "SSIS-123.mp4": "SSIS-123",
            "259LUXU-1111.mkv": "259LUXU-1111",
            "FC2-PPV-123456.mp4": "FC2-123456",
            "FC2-123456.mp4": "FC2-123456",
            "MIDE-139-CD1.mp4": "MIDE-139",
            "sexart.19.11.03.mp4": "sexart.19.11.03",
            "ABC123.mp4": "ABC-123",
            "SIVR-123-CD1.mp4": "SIVR-123",
            "ABP_123.mp4": "ABP_123",
        }

        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                self.assertEqual(getNumber(filename, ""), expected)

    def test_get_number_handles_mixed_edge_cases(self):
        cases = {
            "ABP-123-2024-01-01-CD2.mp4": "ABP-123",
            "ABP-123-cd2.mp4": "ABP-123",
            "FC2-PPV123456-C.mp4": "FC2-123456",
            "sampleABP-123.mp4": "ABP-123",
            "sexart.19.11.03-CD1.mp4": "sexart.19.11.03",
            "abc123.mp4": "abc-123",
        }

        for filename, expected in cases.items():
            with self.subTest(filename=filename):
                escape_string = "sample" if filename.startswith("sample") else ""
                self.assertEqual(getNumber(filename, escape_string), expected)

    def test_movie_lists_filters_hidden_and_excluded_folders(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "keep").mkdir()
            (root / "failed").mkdir()
            (root / "keep" / "a.mp4").write_text("x", encoding="utf-8")
            (root / "keep" / ".hidden.mp4").write_text("x", encoding="utf-8")
            (root / "failed" / "b.mp4").write_text("x", encoding="utf-8")
            (root / "keep" / "nested").mkdir()
            (root / "keep" / "nested" / "c.MKV").write_text("x", encoding="utf-8")

            result = movie_lists("failed", ".mp4|.mkv|.MKV", str(root))
            self.assertEqual(
                result,
                [str(root / "keep" / "a.mp4"), str(root / "keep" / "nested" / "c.MKV")],
            )

    def test_movie_lists_skips_nested_excluded_paths_and_handles_windows_roots(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "keep").mkdir()
            (root / "skip").mkdir()
            (root / "skip" / "nested").mkdir()
            (root / "keep" / "visible.MP4").write_text("x", encoding="utf-8")
            (root / "keep" / ".hidden.mkv").write_text("x", encoding="utf-8")
            (root / "skip" / "nested" / "ignored.mp4").write_text("x", encoding="utf-8")

            windows_root = str(root).replace("/", "\\")
            result = movie_lists("skip", ".mp4|.MP4|.mkv", windows_root)
            self.assertEqual(result, [str(root / "keep" / "visible.MP4")])

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
                self.assertTrue(is_uncensored("HEYZO-1234"))
                self.assertTrue(is_uncensored("123456-7890"))
                self.assertFalse(is_uncensored("ABP-123"))
            finally:
                os.chdir(cwd)

    def test_is_uncensored_matches_builtin_patterns_without_config(self):
        config = ConfigParser()
        config.read_dict({"uncensored": {"uncensored_prefix": "ZZZ"}})

        with patch("core.file_utils.get_config", return_value=config):
            self.assertTrue(is_uncensored("HEYZO-1234"))
            self.assertTrue(is_uncensored("123456-7890"))
            self.assertTrue(is_uncensored("n1234"))
            self.assertFalse(is_uncensored("ABP-123"))

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

    def test_get_config_file_prefers_parent_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            child = root / "child"
            child.mkdir()
            (root / "config.ini").write_text("[common]\nwebsite = parent\n", encoding="utf-8")
            (child / "config.ini").write_text("[common]\nwebsite = child\n", encoding="utf-8")

            cwd = os.getcwd()
            try:
                os.chdir(child)
                self.assertEqual(get_config_file(), "../config.ini")
                config = get_config()
                self.assertEqual(config.get("common", "website"), "parent")
            finally:
                os.chdir(cwd)

    def test_get_config_file_defaults_when_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
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


class ScrapePipelineDispatchTests(unittest.TestCase):
    def setUp(self):
        self.config = ConfigParser()
        self.config.read_dict(
            {
                "Name_Rule": {
                    "naming_media": "number",
                    "naming_file": "title",
                    "folder_name": "title",
                }
            }
        )

    def _movie_payload(self, title="Movie"):
        return {
            "title": title,
            "actor": "[]",
            "website": "site",
            "number": "ABP-123",
            "release": "2024/01/01",
            "studio": "Studio",
            "publisher": "Publisher",
            "year": "2024",
            "outline": "Outline",
            "runtime": "120",
            "director": "Director",
            "actor_photo": {},
            "tag": "[]",
            "cover": "cover.jpg",
            "series": "Series",
            "cover_small": "thumb.jpg",
        }

    def _fake_scrapers(self, responses, call_order):
        def fake_factory(name):
            def fake(*args):
                call_order.append((name, args))
                payload = responses.get(name, self._movie_payload())
                return json.dumps(payload)

            return fake

        return {
            "javbus": SimpleNamespace(
                main=fake_factory("javbus.main"),
                main_uncensored=fake_factory("javbus.main_uncensored"),
                main_us=fake_factory("javbus.main_us"),
            ),
            "javdb": SimpleNamespace(
                main=fake_factory("javdb.main"),
                main_uncensored=fake_factory("javdb.main_uncensored"),
                main_us=fake_factory("javdb.main_us"),
            ),
            "jav321": SimpleNamespace(
                main=fake_factory("jav321.main"),
                main_uncensored=fake_factory("jav321.main_uncensored"),
                main_us=fake_factory("jav321.main_us"),
            ),
            "avsox": SimpleNamespace(
                main=fake_factory("avsox.main"),
                main_uncensored=fake_factory("avsox.main_uncensored"),
                main_us=fake_factory("avsox.main_us"),
            ),
            "mgstage": SimpleNamespace(
                main=fake_factory("mgstage.main"),
                main_uncensored=fake_factory("mgstage.main_uncensored"),
                main_us=fake_factory("mgstage.main_us"),
            ),
            "dmm": SimpleNamespace(
                main=fake_factory("dmm.main"),
                main_uncensored=fake_factory("dmm.main_uncensored"),
                main_us=fake_factory("dmm.main_us"),
            ),
            "xcity": SimpleNamespace(
                main=fake_factory("xcity.main"),
                main_uncensored=fake_factory("xcity.main_uncensored"),
                main_us=fake_factory("xcity.main_us"),
            ),
        }

    def test_mode1_uncensored_tries_expected_chain(self):
        call_order = []
        responses = {
            "javbus.main_uncensored": self._movie_payload(title=""),
            "javdb.main": self._movie_payload(title=""),
            "jav321.main": self._movie_payload(title=""),
            "avsox.main": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=True), \
            patch.object(scrape_pipeline, "getDataState", side_effect=lambda data: 0 if not data.get("title") else 1), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("HEYZO-1234", self.config, 1, "")

        self.assertEqual(
            [name for name, _ in call_order],
            ["javbus.main_uncensored", "javdb.main", "jav321.main", "avsox.main"],
        )
        self.assertEqual(result["title"], "ok")

    def test_mode1_mgstage_chain_uses_normalized_number(self):
        call_order = []
        responses = {
            "mgstage.main": self._movie_payload(title=""),
            "jav321.main": self._movie_payload(title=""),
            "javdb.main": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "getDataState", side_effect=lambda data: 0 if not data.get("title") else 1), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("259LUXU-1111", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["mgstage.main", "jav321.main", "javdb.main"])
        self.assertEqual(call_order[1][1][0], "LUXU-1111")
        self.assertEqual(result["title"], "ok")

    def test_mode2_routes_to_mgstage(self):
        call_order = []
        responses = {"mgstage.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("MIDE-001", self.config, 2, "")

        self.assertEqual([name for name, _ in call_order], ["mgstage.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode3_uses_javbus_uncensored_branch(self):
        call_order = []
        responses = {"javbus.main_uncensored": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=True), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("HEYZO-1234", self.config, 3, "")

        self.assertEqual([name for name, _ in call_order], ["javbus.main_uncensored"])
        self.assertEqual(call_order[0][1], ("HEYZO-1234", ""))
        self.assertEqual(result["title"], "ok")

    def test_mode1_fc2_short_circuits_to_javdb(self):
        call_order = []
        responses = {"javdb.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("FC2-PPV-123456", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javdb.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode1_european_uses_us_chain(self):
        call_order = []
        responses = {
            "javdb.main_us": self._movie_payload(title=""),
            "javbus.main_us": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("sexart.19.11.03", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javdb.main_us", "javbus.main_us"])
        self.assertEqual(result["title"], "ok")

    def test_mode5_routes_european_titles_to_javdb_us_branch(self):
        call_order = []
        responses = {"javdb.main_us": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("sexart.19.11.03", self.config, 5, "")

        self.assertEqual([name for name, _ in call_order], ["javdb.main_us"])
        self.assertEqual(call_order[0][1], ("sexart.19.11.03", ""))
        self.assertEqual(result["title"], "ok")

    def test_mode4_passes_uncensored_flag_to_jav321(self):
        call_order = []
        responses = {"jav321.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=True), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("HEYZO-1234", self.config, 4, "url")

        self.assertEqual([name for name, _ in call_order], ["jav321.main"])
        self.assertEqual(call_order[0][1], ("HEYZO-1234", True, "url"))
        self.assertEqual(result["title"], "ok")

    def test_mode6_routes_to_avsox(self):
        call_order = []
        responses = {"avsox.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("ABP-123", self.config, 6, "")

        self.assertEqual([name for name, _ in call_order], ["avsox.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode7_routes_to_xcity(self):
        call_order = []
        responses = {"xcity.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("ABP-123", self.config, 7, "")

        self.assertEqual([name for name, _ in call_order], ["xcity.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode8_routes_to_dmm(self):
        call_order = []
        responses = {"dmm.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("MIDD-001", self.config, 8, "")

        self.assertEqual([name for name, _ in call_order], ["dmm.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode1_timeout_short_circuits_postprocessing(self):
        call_order = []
        responses = {
            "javbus.main": {
                **self._movie_payload(title="ok"),
                "website": "timeout",
                "release": "2024/01/01",
            }
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("ABP-123", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javbus.main"])
        self.assertEqual(result["website"], "timeout")
        self.assertEqual(result["release"], "2024/01/01")

    def test_mode6_empty_title_short_circuits_postprocessing(self):
        call_order = []
        responses = {
            "avsox.main": {
                **self._movie_payload(title=""),
                "website": "site",
                "release": "2024/01/01",
            }
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("ABP-123", self.config, 6, "")

        self.assertEqual([name for name, _ in call_order], ["avsox.main"])
        self.assertEqual(result["title"], "")
        self.assertEqual(result["release"], "2024/01/01")


if __name__ == "__main__":
    unittest.main()
