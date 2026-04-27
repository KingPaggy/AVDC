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
from core.file_utils import escapePath, getNumber, getDataState, is_uncensored, movie_lists, check_pic
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

    def test_escape_path_empty_literals(self):
        config = ConfigParser()
        config.read_dict({"escape": {"literals": ""}})
        self.assertEqual(
            escapePath(r"C:\foo\bar", config),
            r"C:\foo\bar",
        )

    def test_escape_path_no_escape_chars(self):
        config = ConfigParser()
        config.read_dict({"escape": {"literals": ":|?"}})
        self.assertEqual(
            escapePath(r"C:\foo\bar", config),
            r"C:\foo\bar",
        )

    def test_get_number_xxx_av_format(self):
        self.assertEqual(getNumber("XXX-AV-12345.mp4", ""), "XXX-AV-12345")
        # XXX-AV regex uses upper(), so lowercase input returns uppercase result
        self.assertEqual(getNumber("xxx-av-9999.mp4", ""), "XXX-AV-9999")

    def test_get_number_escape_removes_all(self):
        result = getNumber("sample-ABP-123.mp4", "sample-ABP-123")
        self.assertEqual(result, "")

    def test_get_number_dmm_style_no_separator(self):
        self.assertEqual(getNumber("abcd00123.mp4", ""), "abcd00123")
        self.assertEqual(getNumber("ABCDE00999.mp4", ""), "ABCDE00999")

    def test_get_number_fallback_pure_digits(self):
        self.assertEqual(getNumber("123456.mp4", ""), "123456")

    def test_get_number_fallback_pure_alpha(self):
        self.assertEqual(getNumber("abcdef.mp4", ""), "abcdef")

    def test_get_number_short_alpha_num_fallback(self):
        # "AB123" has no "-" or "_", falls to else branch
        # find_char=["AB"], find_num=["123"], len(find_num[0])=3 <= 4, len(find_char[0])=2 > 1
        self.assertEqual(getNumber("AB123.mp4", ""), "AB-123")

    def test_get_number_exception_fallback(self):
        # Trigger exception path by causing an indexing error on split
        self.assertEqual(getNumber("!!!.mp4", ""), "!!!")

    def test_check_pic_valid_image(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            from PIL import Image
            img = Image.new("RGB", (100, 100), color="red")
            img.save(f.name)
            f.flush()
            try:
                self.assertTrue(check_pic(f.name))
            finally:
                os.unlink(f.name)

    def test_check_pic_missing_file(self):
        self.assertFalse(check_pic("/nonexistent/path/image.jpg"))

    def test_check_pic_corrupted_file(self):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"not an image")
            f.flush()
            try:
                self.assertFalse(check_pic(f.name))
            finally:
                os.unlink(f.name)

    def test_movie_lists_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = movie_lists("", ".mp4|.mkv", tmpdir)
            self.assertEqual(result, [])

    def test_movie_lists_no_matching_extensions(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "video.txt").write_text("x", encoding="utf-8")
            (root / "video.doc").write_text("x", encoding="utf-8")
            result = movie_lists("", ".mp4|.mkv", str(root))
            self.assertEqual(result, [])

    def test_movie_lists_multiple_escape_folders_comma(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "skip1").mkdir()
            (root / "skip2").mkdir()
            (root / "keep").mkdir()
            (root / "skip1" / "a.mp4").write_text("x", encoding="utf-8")
            (root / "skip2" / "b.mp4").write_text("x", encoding="utf-8")
            (root / "keep" / "c.mp4").write_text("x", encoding="utf-8")

            result = movie_lists("skip1,skip2", ".mp4", str(root))
            self.assertEqual(result, [str(root / "keep" / "c.mp4")])

    def test_movie_lists_multiple_escape_folders_chinese_comma(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "alpha").mkdir()
            (root / "beta").mkdir()
            (root / "alpha" / "a.mp4").write_text("x", encoding="utf-8")
            (root / "beta" / "b.mp4").write_text("x", encoding="utf-8")

            result = movie_lists("alpha，beta", ".mp4", str(root))
            self.assertEqual(result, [])

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

        with patch("core.config_io.get_config", return_value=config):
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

    def test_get_info_all_fields_populated(self):
        data = {
            "title": "Movie",
            "studio": "Studio",
            "publisher": "Publisher",
            "year": "2024",
            "outline": "Outline",
            "runtime": "120",
            "director": "Director",
            "actor_photo": {"Actor": "url"},
            "actor": "Actor",
            "release": "2024-01-01",
            "tag": ["tag1"],
            "number": "ABP-123",
            "cover": "cover.jpg",
            "website": "javbus",
            "series": "Series",
        }

        result = get_info(data)
        self.assertEqual(result[0], "Movie")
        self.assertEqual(result[1], "Studio")
        self.assertEqual(result[2], "Publisher")
        self.assertEqual(result[3], "2024")
        self.assertEqual(result[4], "Outline")
        self.assertEqual(result[5], "120")
        self.assertEqual(result[6], "Director")
        self.assertEqual(result[7], {"Actor": "url"})
        self.assertEqual(result[8], "Actor")
        self.assertEqual(result[9], "2024-01-01")
        self.assertEqual(result[10], ["tag1"])
        self.assertEqual(result[11], "ABP-123")
        self.assertEqual(result[12], "cover.jpg")
        self.assertEqual(result[13], "javbus")
        self.assertEqual(result[14], "Series")


class ScrapePipelineDispatchTests(unittest.TestCase):
    def setUp(self):
        from core.scraper_adapter import clear_cache
        clear_cache()
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

    def test_mode1_dmm_style_no_separator_routes_to_dmm(self):
        """mode 1 DMM 风格无分隔符 → dmm.main"""
        call_order = []
        responses = {"dmm.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("abcd00123", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["dmm.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode1_dmm_style_with_separator_uses_standard_chain(self):
        """mode 1 DMM 风格含分隔符 → 走标准链 (因为有 - 或 _)"""
        call_order = []
        responses = {
            "javbus.main": self._movie_payload(title=""),
            "jav321.main": self._movie_payload(title=""),
            "xcity.main": self._movie_payload(title=""),
            "javdb.main": self._movie_payload(title=""),
            "avsox.main": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("abcd-00123", self.config, 1, "")

        names = [name for name, _ in call_order]
        self.assertEqual(names, ["javbus.main", "jav321.main", "xcity.main", "javdb.main", "avsox.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode1_standard_uses_full_fallback_chain(self):
        """mode 1 标准编号: javbus → jav321 → xcity → javdb → avsox"""
        call_order = []
        responses = {
            "javbus.main": self._movie_payload(title=""),
            "jav321.main": self._movie_payload(title=""),
            "xcity.main": self._movie_payload(title=""),
            "javdb.main": self._movie_payload(title=""),
            "avsox.main": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        names = [name for name, _ in call_order]
        self.assertEqual(names, ["javbus.main", "jav321.main", "xcity.main", "javdb.main", "avsox.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode1_standard_first_scraper_succeeds(self):
        """mode 1 标准编号: javbus 直接成功"""
        call_order = []
        responses = {"javbus.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javbus.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode3_javbus_standard_branch(self):
        """mode 3 非 uncensored/非 european → javbus.main"""
        call_order = []
        responses = {"javbus.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 3, "")

        self.assertEqual([name for name, _ in call_order], ["javbus.main"])
        self.assertEqual(result["title"], "ok")

    def test_mode3_javbus_european_branch(self):
        """mode 3 european → javbus.main_us"""
        call_order = []
        responses = {"javbus.main_us": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("sexart.19.11.03", self.config, 3, "")

        self.assertEqual([name for name, _ in call_order], ["javbus.main_us"])
        self.assertEqual(result["title"], "ok")

    def test_mode5_javdb_standard_branch(self):
        """mode 5 非 european → javdb.main(isuncensored)"""
        call_order = []
        responses = {"javdb.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=True), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("HEYZO-1234", self.config, 5, "")

        self.assertEqual([name for name, _ in call_order], ["javdb.main"])
        self.assertEqual(call_order[0][1], ("HEYZO-1234", "", True))
        self.assertEqual(result["title"], "ok")

    def test_postprocessing_handles_missing_cover_small(self):
        """postprocessing 中 cover_small 缺失时设为空字符串"""
        call_order = []
        payload = self._movie_payload(title="ok")
        del payload["cover_small"]
        responses = {"javbus.main": payload}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        self.assertEqual(result["cover_small"], "")

    def test_mode1_dmm_like_early_returns_empty_for_non_mode7(self):
        """mode != 1 且非 2-8 的 DMM 风格编号返回空占位"""
        # mode 9 doesn't exist, but if we pass a mode that's not matched
        # and the number matches DMM pattern with mode != 7, it returns early
        # Actually line 67: re.match DMM pattern and mode != 7 → returns empty
        # Let's test mode 9 with DMM pattern
        fake_scrapers = self._fake_scrapers({}, [])
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("abcd00123", self.config, 9, "")

        self.assertEqual(result["title"], "")
        self.assertEqual(result["actor"], "")
        self.assertEqual(result["website"], "")

    def test_postprocessing_normalizes_actor_empty_list(self):
        """actor 为空列表时设为 Unknown"""
        call_order = []
        payload = self._movie_payload(title="ok")
        payload["actor"] = "[]"
        responses = {"javbus.main": payload}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        self.assertEqual(result["actor"], "Unknown")

    def test_postprocessing_sanitizes_title_special_chars(self):
        """title 中的特殊字符被移除，空格被替换为点"""
        call_order = []
        payload = self._movie_payload(title="Movie With Special Chars")
        responses = {"javbus.main": payload}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        self.assertNotIn(" ", result["title"])
        self.assertIn(".", result["title"])  # space replaced with .

    def test_postprocessing_normalizes_release_date_separator(self):
        """release 中的 / 被替换为 -"""
        call_order = []
        payload = self._movie_payload(title="ok")
        payload["release"] = "2024/01/15"
        responses = {"javbus.main": payload}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        self.assertEqual(result["release"], "2024-01-15")

    def test_postprocessing_cleans_studio_director_series_publisher(self):
        """studio/director/series/publisher 中的 / 被移除"""
        call_order = []
        payload = self._movie_payload(title="ok")
        payload["studio"] = "Studio/Name"
        payload["director"] = "Dir/ector"
        responses = {"javbus.main": payload}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            result = scrape_pipeline.getDataFromJSON("SSIS-123", self.config, 1, "")

        self.assertEqual(result["studio"], "StudioName")
        self.assertEqual(result["director"], "Director")

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


# ========================================================================
# Real-number scraping integration tests
# Uses real video numbers from each supported category, mocks network layer.
# Run as part of the regular test suite to verify dispatch routing stays correct.
# ========================================================================

class RealNumberDispatchTests(unittest.TestCase):
    """Verify that real-world video numbers are dispatched to the correct scrapers."""

    def setUp(self):
        from core.scraper_adapter import clear_cache
        clear_cache()
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
            "number": "TEST-123",
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


class RealNumberExtractTests(RealNumberDispatchTests):
    """Test getNumber() with real video file names."""

    def test_ssni_standard_censored(self):
        self.assertEqual(getNumber("SSNI-487.mp4", ""), "SSNI-487")

    def test_abp_standard_censored(self):
        self.assertEqual(getNumber("ABP-647-C.mp4", ""), "ABP-647")

    def test_ssis_with_disc_suffix(self):
        self.assertEqual(getNumber("SSIS-487-CD1.mp4", ""), "SSIS-487")

    def test_heyzo_uncensored(self):
        self.assertEqual(getNumber("HEYZO-3032.mp4", ""), "HEYZO-3032")

    def test_fc2_with_ppv(self):
        self.assertEqual(getNumber("FC2-PPV-3052557.mp4", ""), "FC2-3052557")

    def test_fc2_without_ppv(self):
        self.assertEqual(getNumber("FC2-1234567.mp4", ""), "FC2-1234567")

    def test_european_format(self):
        self.assertEqual(getNumber("sexart.19.11.03.mp4", ""), "sexart.19.11.03")

    def test_mgstyle_mixed_number(self):
        self.assertEqual(getNumber("259LUXU-504.mp4", ""), "259LUXU-504")

    def test_dmm_style_no_separator(self):
        self.assertEqual(getNumber("h_001abcd12345.mp4", ""), "h_001abcd12345")

    def test_number_with_date_and_disc(self):
        self.assertEqual(getNumber("SSIS-123-2024-03-15-CD2.mp4", ""), "SSIS-123")


class RealNumberUncensoredTests(RealNumberDispatchTests):
    """Test is_uncensored() with real number patterns."""

    def test_ssni_not_uncensored(self):
        self.assertFalse(is_uncensored("SSNI-487"))

    def test_heyzo_is_uncensored(self):
        self.assertTrue(is_uncensored("HEYZO-3032"))

    def test_all_digit_pattern_is_uncensored(self):
        self.assertTrue(is_uncensored("111111-001"))

    def test_fc2_not_uncensored(self):
        self.assertFalse(is_uncensored("FC2-3052557"))

    def test_european_not_uncensored(self):
        self.assertFalse(is_uncensored("sexart.19.11.03"))

    def test_n_prefix_is_uncensored(self):
        self.assertTrue(is_uncensored("n1234"))


class RealNumberDispatchRoutingTests(RealNumberDispatchTests):
    """Test that real numbers are dispatched to the correct scraper chain."""

    def test_ssni_uses_standard_chain(self):
        """SSIS-487 → javbus → jav321 → xcity → javdb → avsox"""
        call_order = []
        responses = {"javbus.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            scrape_pipeline.getDataFromJSON("SSIS-487", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javbus.main"])

    def test_heyzo_uses_uncensored_chain(self):
        """HEYZO-3032 → javbus.uncensored → javdb → jav321 → avsox"""
        call_order = []
        responses = {
            "javbus.main_uncensored": self._movie_payload(title=""),
            "javdb.main": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=True), \
            patch.object(scrape_pipeline, "getDataState", side_effect=lambda data: 0 if not data.get("title") else 1), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            scrape_pipeline.getDataFromJSON("HEYZO-3032", self.config, 1, "")

        names = [name for name, _ in call_order]
        self.assertEqual(names, ["javbus.main_uncensored", "javdb.main"])

    def test_fc2_uses_javdb_only(self):
        """FC2-3052557 → javdb"""
        call_order = []
        responses = {"javdb.main": self._movie_payload(title="ok")}
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            scrape_pipeline.getDataFromJSON("FC2-3052557", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javdb.main"])

    def test_european_uses_us_chain(self):
        """sexart.19.11.03 → javdb.us → javbus.us"""
        call_order = []
        responses = {
            "javdb.main_us": self._movie_payload(title=""),
            "javbus.main_us": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "getDataState", side_effect=lambda data: 0 if not data.get("title") else 1), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            scrape_pipeline.getDataFromJSON("sexart.19.11.03", self.config, 1, "")

        self.assertEqual([name for name, _ in call_order], ["javdb.main_us", "javbus.main_us"])

    def test_mgstyle_uses_mgstage_chain(self):
        """259LUXU-504 → mgstage → jav321 → javdb → javbus"""
        call_order = []
        responses = {
            "mgstage.main": self._movie_payload(title=""),
            "jav321.main": self._movie_payload(title="ok"),
        }
        fake_scrapers = self._fake_scrapers(responses, call_order)
        with patch.object(scrape_pipeline, "is_uncensored", return_value=False), \
            patch.object(scrape_pipeline, "getDataState", side_effect=lambda data: 0 if not data.get("title") else 1), \
            patch.object(scrape_pipeline, "get_scraper_modules", return_value=fake_scrapers):
            scrape_pipeline.getDataFromJSON("259LUXU-504", self.config, 1, "")

        names = [name for name, _ in call_order]
        self.assertEqual(names, ["mgstage.main", "jav321.main"])


if __name__ == "__main__":
    unittest.main()
