#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import types
import unittest


fake_gethtml = types.ModuleType("Function.getHtml")
fake_gethtml.get_config = lambda: ("no", "", 0, 1)
fake_gethtml.get_proxies = lambda proxy_type, proxy: {}
sys.modules.setdefault("Function.getHtml", fake_gethtml)

from application.remote_service import RemoteService


class RemoteServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = RemoteService()

    def test_show_actor_lines_filters_by_mode(self):
        actor_list = {
            "TotalRecordCount": 3,
            "Items": [
                {"Name": "A", "ImageTags": {}},
                {"Name": "B", "ImageTags": {"x": "y"}},
                {"Name": "C", "ImageTags": {}},
            ],
        }

        self.assertEqual(
            self.service.show_actor_lines(actor_list, 1),
            ["[+]1.A,2.C,"],
        )
        self.assertEqual(
            self.service.show_actor_lines(actor_list, 2),
            ["[+]1.B,"],
        )
        self.assertEqual(
            self.service.show_actor_lines(actor_list, 3),
            ["[+]1.A,2.B,3.C,"],
        )

    def test_choose_picture_name_accepts_aliases(self):
        flag, pic = self.service.choose_picture_name("A (B)", ["B.jpg"])
        self.assertEqual((flag, pic), (1, "B.jpg"))

    def test_find_profile_pictures_builds_lines_without_upload(self):
        actor_list = {
            "Items": [
                {"Name": "A", "ImageTags": {}, "Id": "1"},
                {"Name": "B", "ImageTags": {"x": "y"}, "Id": "2"},
            ]
        }
        lines = self.service.find_profile_pictures(
            2,
            actor_list,
            ["A.jpg", "B.png"],
            "/tmp/Success",
            "http://localhost:8096",
            "key",
            lambda msg: None,
            upload_enabled=False,
        )
        self.assertEqual(
            lines,
            [
                "[+]   1.Actor name: A  Pic name: A.jpg",
                "[+]   2.Actor name: B  Pic name: B.png",
            ],
        )


if __name__ == "__main__":
    unittest.main()
