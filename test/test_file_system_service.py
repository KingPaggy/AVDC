#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
import xml.etree.ElementTree as ET
from configparser import ConfigParser
from pathlib import Path

from application.file_system_service import FileSystemService


class FileSystemServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = FileSystemService()
        self.config = ConfigParser()
        self.config.read_dict(
            {
                "escape": {"literals": ":|?"},
            }
        )

    def test_get_part(self):
        self.assertEqual(self.service.get_part("/tmp/ABP-123-CD1.mp4"), "-CD1")
        self.assertEqual(self.service.get_part("/tmp/ABP-123-cd2.mp4"), "-cd2")

    def test_create_folder(self):
        json_data = {
            "folder_name": "title-number",
            "title": "Movie",
            "studio": "Studio",
            "publisher": "Publisher",
            "year": "2024",
            "outline": "",
            "runtime": "120",
            "director": "Director",
            "actor_photo": {},
            "actor": "Actor",
            "release": "2024-01-01",
            "tag": [],
            "number": "ABP-123",
            "cover": "cover.jpg",
            "website": "site",
            "series": "Series",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            path = self.service.create_folder(tmpdir, json_data, self.config)
            self.assertTrue(Path(path).exists())
            self.assertIn("Movie-ABP-123", path)

    def test_paste_file_to_folder_moves_video_and_subtitles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src = root / "ABP-123.mp4"
            sub = root / "ABP-123.srt"
            src.write_text("video", encoding="utf-8")
            sub.write_text("sub", encoding="utf-8")

            target = root / "out"
            target.mkdir()
            logs = []

            def log(message):
                logs.append(message)

            def move_failed(filepath, failed_folder):
                logs.append(f"failed:{filepath}")

            result = self.service.paste_file_to_folder(
                str(src),
                str(target),
                "ABP-123",
                str(root / "failed"),
                True,
                False,
                [".srt"],
                log,
                move_failed,
            )

            self.assertTrue(result)
            self.assertTrue((target / "ABP-123.mp4").exists())
            self.assertTrue((target / "ABP-123.srt").exists())

    def test_cleanup_empty_dirs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            empty_dir = root / "a" / "b"
            empty_dir.mkdir(parents=True)
            logs = []

            self.service.cleanup_empty_dirs(str(root), logs.append)

            self.assertFalse(empty_dir.exists())

    # -------------------------------------------------------------------
    # NFO generation tests
    # -------------------------------------------------------------------

    def _movie_data(self, **overrides):
        data = {
            "title": "Movie",
            "studio": "Studio",
            "publisher": "Publisher",
            "year": "2024",
            "outline": "Plot",
            "runtime": "120",
            "director": "Director",
            "actor_photo": {},
            "actor": "Actor A,Actor B",
            "release": "2024-01-01",
            "tag": ["tag1", "tag2"],
            "number": "SSIS-487",
            "cover": "cover.jpg",
            "website": "javbus",
            "series": "Series",
            "naming_media": "number-title",
        }
        data.update(overrides)
        return data

    def test_write_nfo_generates_valid_xml(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs = []
            self.service.write_nfo(
                tmpdir, "SSIS-487", 0, 0,
                self._movie_data(),
                "/input/test.mp4", "/input/failed",
                True, logs.append, lambda a, b: None,
            )
            nfo_path = Path(tmpdir) / "SSIS-487.nfo"
            self.assertTrue(nfo_path.exists())
            # Parse as XML to verify well-formedness
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            self.assertEqual(root.tag, "movie")
            self.assertEqual(root.find("title").text, "Movie")
            self.assertEqual(root.find("number").text, "SSIS-487")

    def test_write_nfo_escapes_xml_special_chars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs = []
            self.service.write_nfo(
                tmpdir, "SSIS-487", 0, 0,
                self._movie_data(title="A & B <C> \"D\" 'E'"),
                "/input/test.mp4", "/input/failed",
                True, logs.append, lambda a, b: None,
            )
            nfo_path = Path(tmpdir) / "SSIS-487.nfo"
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            # XML should be parseable with special chars properly escaped
            self.assertEqual(root.find("title").text, "A & B <C> \"D\" 'E'")

    def test_write_nfo_multi_actor_tags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs = []
            self.service.write_nfo(
                tmpdir, "SSIS-487", 0, 0,
                self._movie_data(actor="枫,安齋"),
                "/input/test.mp4", "/input/failed",
                True, logs.append, lambda a, b: None,
            )
            nfo_path = Path(tmpdir) / "SSIS-487.nfo"
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            actors = root.findall("actor")
            self.assertEqual(len(actors), 2)
            names = [a.find("name").text for a in actors]
            self.assertIn("枫", names)
            self.assertIn("安齋", names)

    def test_write_nfo_multi_genre_tags(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs = []
            self.service.write_nfo(
                tmpdir, "SSIS-487", 0, 0,
                self._movie_data(tag=["巨乳", "騎乗位"]),
                "/input/test.mp4", "/input/failed",
                True, logs.append, lambda a, b: None,
            )
            nfo_path = Path(tmpdir) / "SSIS-487.nfo"
            tree = ET.parse(nfo_path)
            root = tree.getroot()
            genres = root.findall("genre")
            self.assertEqual(len(genres), 2)
            genre_texts = [g.text for g in genres]
            self.assertIn("巨乳", genre_texts)
            self.assertIn("騎乗位", genre_texts)

    def test_write_nfo_skips_if_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logs = []
            # Write once
            self.service.write_nfo(
                tmpdir, "SSIS-487", 0, 0,
                self._movie_data(),
                "/input/test.mp4", "/input/failed",
                True, logs.append, lambda a, b: None,
            )
            original_content = Path(tmpdir, "SSIS-487.nfo").read_text()
            # Write again with different data
            self.service.write_nfo(
                tmpdir, "SSIS-487", 0, 0,
                self._movie_data(title="Changed"),
                "/input/test.mp4", "/input/failed",
                True, logs.append, lambda a, b: None,
            )
            # Content should not change
            self.assertEqual(Path(tmpdir, "SSIS-487.nfo").read_text(), original_content)
            self.assertIn("[+]Nfo Existed!", "\n".join(logs))

    # -------------------------------------------------------------------
    # File operation tests
    # -------------------------------------------------------------------

    def test_move_movie_files_moves_videos_and_subtitles(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            src1 = root / "ABP-123.mp4"
            src2 = root / "SSIS-456.mkv"
            sub1 = root / "ABP-123.srt"
            src1.write_text("x", encoding="utf-8")
            src2.write_text("x", encoding="utf-8")
            sub1.write_text("x", encoding="utf-8")

            logs = []
            self.service.move_movie_files(
                [str(src1), str(src2)],
                str(root / "dest"),
                [".srt"],
                logs.append,
            )

            self.assertTrue((root / "dest" / "ABP-123.mp4").exists())
            self.assertTrue((root / "dest" / "SSIS-456.mkv").exists())
            self.assertTrue((root / "dest" / "ABP-123.srt").exists())

    def test_copy_fanart_copies_thumb(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            thumb = root / "SSIS-487-thumb.jpg"
            thumb.write_bytes(b"x" * 100)

            logs = []
            self.service.copy_fanart(str(root), "SSIS-487", logs.append)

            self.assertTrue((root / "SSIS-487-fanart.jpg").exists())

    def test_delete_thumb_respects_keep_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            thumb = root / "SSIS-487-thumb.jpg"
            thumb.write_bytes(b"x" * 100)

            # keep_thumb=False → delete
            self.service.delete_thumb(str(root), "SSIS-487", False, lambda m: None)
            self.assertFalse(thumb.exists())

            # Re-create
            thumb.write_bytes(b"x" * 100)
            # keep_thumb=True → keep
            self.service.delete_thumb(str(root), "SSIS-487", True, lambda m: None)
            self.assertTrue(thumb.exists())

    def test_fix_size_skips_when_ratio_correct(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create a poster with correct 2:3 ratio
            poster = root / "SSIS-487-poster.jpg"
            img = Image.new("RGB", (200, 300), color="red")
            img.save(poster)
            original_mtime = poster.stat().st_mtime

            logs = []
            self.service.fix_size(str(root), "SSIS-487", logs.append)

            # File should not have been modified
            self.assertAlmostEqual(poster.stat().st_mtime, original_mtime, delta=1)

    def test_fix_size_resizes_when_ratio_wrong(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            # Create a wide poster (wrong ratio)
            poster = root / "SSIS-487-poster.jpg"
            img = Image.new("RGB", (400, 200), color="blue")
            img.save(poster)
            orig_w, orig_h = img.size
            img.close()

            logs = []
            self.service.fix_size(str(root), "SSIS-487", logs.append)

            # Should have been resized to 2:3
            with Image.open(poster) as resized:
                w, h = resized.size
                self.assertAlmostEqual(w / h, 2 / 3, delta=0.05)


if __name__ == "__main__":
    unittest.main()
