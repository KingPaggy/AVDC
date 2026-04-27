#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from configparser import ConfigParser

from application.file_processing_service import FileProcessDependencies, FileProcessingService


class FileProcessingServiceTests(unittest.TestCase):
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

    def _deps(self, events, json_data, move_mode=True):
        def log(message):
            events.append(("log", message))

        def debug(data):
            events.append(("debug", data["title"]))

        def get_json_data(mode, number, config, appoint_url):
            events.append(("get_json_data", mode, number, appoint_url))
            return dict(json_data)

        def create_folder(success_folder, movie_json, config):
            events.append(("create_folder", success_folder))
            return "/output/movie"

        def get_part(filepath, failed_folder):
            events.append(("get_part", filepath))
            return "-CD1"

        def get_naming_rule(movie_json):
            return "title-number"

        def move_failed_folder(filepath, failed_folder):
            events.append(("move_failed_folder", filepath, failed_folder))

        def thumb_download(*args):
            events.append(("thumb_download", args[1]))

        def small_cover_download(*args):
            events.append(("small_cover_download", args[1]))
            return ""

        def cut_image(*args):
            events.append(("cut_image", args[1]))

        def fix_size(*args):
            events.append(("fix_size", args[0]))

        def copy_fanart(*args):
            events.append(("copy_fanart", args[0]))

        def delete_thumb(*args):
            events.append(("delete_thumb", args[0]))

        def paste_file(*args):
            events.append(("paste_file", args[0]))
            return True

        def print_files(*args):
            events.append(("print_files", args[0]))

        def extrafanart_download(*args):
            events.append(("extrafanart_download", args[1]))

        def add_mark(*args):
            events.append(("add_mark", args[0]))

        def add_label_info(movie_json):
            events.append(("add_label_info", movie_json["number"]))

        def register_result(count_claw, count, movie_json):
            events.append(("register_result", count_claw, count, movie_json["number"]))

        return FileProcessDependencies(
            log=log,
            debug=debug,
            get_json_data=get_json_data,
            create_folder=create_folder,
            get_part=get_part,
            get_naming_rule=get_naming_rule,
            move_failed_folder=move_failed_folder,
            thumb_download=thumb_download,
            small_cover_download=small_cover_download,
            cut_image=cut_image,
            fix_size=fix_size,
            copy_fanart=copy_fanart,
            delete_thumb=delete_thumb,
            paste_file=paste_file,
            print_files=print_files,
            extrafanart_download=extrafanart_download,
            add_mark=add_mark,
            add_label_info=add_label_info,
            register_result=register_result,
            is_debug_enabled=lambda: True,
            is_program_mode_move=lambda: move_mode,
            is_show_small_cover=lambda: True,
            is_copy_fanart_enabled=lambda: True,
            is_print_enabled=lambda: True,
            is_extrafanart_enabled=lambda: True,
            is_restore_imagecut_enabled=lambda: True,
        )

    def test_process_runs_full_flow(self):
        events = []
        deps = self._deps(
            events,
            {
                "title": "Movie",
                "website": "site",
                "cover": "http://example.com/a.jpg",
                "cover_small": "http://example.com/b.jpg",
                "imagecut": 0,
                "number": "ABP-123",
                "actor": "[]",
                "release": "2024/01/01",
                "studio": "Studio",
                "publisher": "Publisher",
                "year": "2024",
                "outline": "Outline",
                "runtime": "120",
                "director": "Director",
                "actor_photo": {},
                "tag": [],
                "series": "Series",
                "extrafanart": [],
            },
        )
        service = FileProcessingService()

        result = service.process(
            filepath="/input/ABP-123.mp4",
            number="ABP-123",
            mode=1,
            count_claw=2,
            count=1,
            config=self.config,
            movie_path="/input",
            failed_folder="/input/failed",
            success_folder="/input/output",
            appoint_url="",
            deps=deps,
        )

        self.assertEqual(result, "")
        self.assertIn(("get_json_data", 1, "ABP-123", ""), events)
        self.assertIn(("register_result", 2, 1, "ABP-123"), events)
        self.assertIn(("paste_file", "/input/ABP-123.mp4"), events)

    def test_process_not_found_moves_failed(self):
        events = []
        deps = self._deps(
            events,
            {
                "title": "",
                "website": "site",
                "cover": "http://example.com/a.jpg",
                "cover_small": "",
                "imagecut": 0,
                "number": "ABP-123",
                "actor": "[]",
                "release": "2024/01/01",
                "studio": "Studio",
                "publisher": "Publisher",
                "year": "2024",
                "outline": "Outline",
                "runtime": "120",
                "director": "Director",
                "actor_photo": {},
                "tag": [],
                "series": "Series",
                "extrafanart": [],
            },
        )
        service = FileProcessingService()

        result = service.process(
            filepath="/input/ABP-123.mp4",
            number="ABP-123",
            mode=1,
            count_claw=2,
            count=1,
            config=self.config,
            movie_path="/input",
            failed_folder="/input/failed",
            success_folder="/input/output",
            appoint_url="",
            deps=deps,
        )

        self.assertEqual(result, "not found")
        self.assertIn(("move_failed_folder", "/input/ABP-123.mp4", "/input/failed"), events)


if __name__ == "__main__":
    unittest.main()
