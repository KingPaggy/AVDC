#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()

