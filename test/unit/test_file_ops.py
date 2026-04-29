"""Tests for Function/file_ops.py"""
import os
import shutil
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import patch, MagicMock

import pytest

from core._config.config import AppConfig
from core._files.file_operations import (
    download_file,
    download_thumb,
    download_small_cover,
    download_extrafanart,
    write_nfo,
    move_to_failed,
    paste_file_to_folder,
    copy_as_fanart,
    delete_thumb,
    get_disc_part,
    create_output_folder,
    resolve_naming_rule,
    ensure_failed_folder,
    clean_empty_dirs,
)


# ---- 1.1 下载 ----

class TestDownloadFile:
    def test_success(self, tmp_dir):
        config = AppConfig(timeout=5, retry=3, proxy_type="no")
        mock_resp = MagicMock()
        mock_resp.content = b"fake-image-data"
        with patch("core._files.file_operations.requests.get", return_value=mock_resp):
            ok = download_file("http://example.com/img.jpg", "img.jpg", tmp_dir, config)
        assert ok is True
        assert os.path.exists(os.path.join(tmp_dir, "img.jpg"))

    def test_retry_then_fail(self, tmp_dir):
        config = AppConfig(timeout=2, retry=2, proxy_type="no")
        with patch("core._files.file_operations.requests.get", side_effect=Exception("network error")):
            ok = download_file("http://example.com/img.jpg", "img.jpg", tmp_dir, config)
        assert ok is False

    def test_uses_proxy(self, tmp_dir):
        config = AppConfig(timeout=5, retry=1, proxy_type="http", proxy="127.0.0.1:7890")
        mock_resp = MagicMock()
        mock_resp.content = b"data"
        with patch("core._files.file_operations.requests.get", return_value=mock_resp) as mock_get:
            download_file("http://example.com/img.jpg", "img.jpg", tmp_dir, config)
        _, kwargs = mock_get.call_args
        assert kwargs["proxies"] == {"http": "http://127.0.0.1:7890"}


class TestMoveToFailed:
    def test_moves_when_enabled(self, tmp_dir):
        src = os.path.join(tmp_dir, "video.mp4")
        failed = os.path.join(tmp_dir, "failed")
        os.makedirs(failed)
        open(src, "w").close()
        config = AppConfig(failed_file_move=1)
        move_to_failed(src, failed, config)
        assert os.path.exists(os.path.join(failed, "video.mp4"))

    def test_skips_when_disabled(self, tmp_dir):
        src = os.path.join(tmp_dir, "video.mp4")
        failed = os.path.join(tmp_dir, "failed")
        os.makedirs(failed)
        open(src, "w").close()
        config = AppConfig(failed_file_move=0)
        move_to_failed(src, failed, config)
        assert os.path.exists(src)


# ---- 1.2 NFO ----

class TestWriteNfo:
    def _sample_json(self):
        return {
            "title": "Test Title",
            "number": "SSIS-123",
            "actor": "Alice,Bob",
            "studio": "S1",
            "publisher": "Will",
            "year": "2021",
            "outline": "An outline",
            "runtime": "120",
            "director": "Tanaka",
            "release": "2021-05-01",
            "tag": ["tag1", "tag2"],
            "cover": "http://example.com/cover.jpg",
            "cover_small": "",
            "website": "http://javbus.com/SSIS-123",
            "series": "Super Series",
            "actor_photo": {"Alice": "http://a.jpg", "Bob": ""},
            "naming_media": "number-title",
            "naming_file": "number",
            "folder_name": "number",
            "score": "8.5",
            "imagecut": 1,
            "extrafanart": [],
            "source": "javbus",
        }

    def test_creates_valid_xml(self, tmp_dir):
        json_data = self._sample_json()
        config = AppConfig()
        write_nfo(tmp_dir, "SSIS-123", 0, 0, json_data, config=config)
        nfo_path = os.path.join(tmp_dir, "SSIS-123.nfo")
        assert os.path.exists(nfo_path)
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        assert root.tag == "movie"
        assert root.find("title").text == "SSIS-123-Test Title"
        assert root.find("num").text == "SSIS-123"
        assert root.find("rating").text == "8.5"

    def test_no_duplicate_nfo(self, tmp_dir):
        json_data = self._sample_json()
        config = AppConfig()
        write_nfo(tmp_dir, "SSIS-123", 0, 0, json_data, config=config)
        # Second call should not overwrite
        mtime1 = os.path.getmtime(os.path.join(tmp_dir, "SSIS-123.nfo"))
        write_nfo(tmp_dir, "SSIS-123", 0, 0, json_data, config=config)
        mtime2 = os.path.getmtime(os.path.join(tmp_dir, "SSIS-123.nfo"))
        assert mtime1 == mtime2

    def test_uncensored_tags(self, tmp_dir):
        json_data = self._sample_json()
        json_data["imagecut"] = 3
        config = AppConfig()
        write_nfo(tmp_dir, "UNC-001", 0, 0, json_data, config=config)
        tree = ET.parse(os.path.join(tmp_dir, "UNC-001.nfo"))
        tags = [el.text for el in tree.getroot().findall("tag")]
        assert "無碼" in tags

    def test_cn_sub_and_leak_tags(self, tmp_dir):
        json_data = self._sample_json()
        config = AppConfig()
        write_nfo(tmp_dir, "SSIS-123", cn_sub=1, leak=1, json_data=json_data, config=config)
        tree = ET.parse(os.path.join(tmp_dir, "SSIS-123.nfo"))
        tags = [el.text for el in tree.getroot().findall("tag")]
        assert "中文字幕" in tags
        assert "流出" in tags

    def test_xml_escapes_special_chars(self, tmp_dir):
        json_data = self._sample_json()
        json_data["title"] = "Title <with> &special 'chars'"
        config = AppConfig()
        write_nfo(tmp_dir, "SSIS-123", 0, 0, json_data, config=config)
        # Should not raise XML parse error
        tree = ET.parse(os.path.join(tmp_dir, "SSIS-123.nfo"))
        assert tree.getroot().find("title") is not None


# ---- 1.3 移动/整理/命名 ----

class TestGetDiscPart:
    def test_cd_upper(self):
        assert get_disc_part("/path/to/SSIS-123-CD1.mp4") == "-CD1"

    def test_cd_lower(self):
        assert get_disc_part("/path/to/ssis-123-cd2.mp4") == "-cd2"

    def test_no_disc(self):
        assert get_disc_part("/path/to/SSIS-123.mp4") == ""


class TestCopyAsFanart:
    def test_copies_thumb(self, tmp_dir):
        thumb = os.path.join(tmp_dir, "SSIS-123-thumb.jpg")
        open(thumb, "w").close()
        copy_as_fanart(tmp_dir, "SSIS-123")
        assert os.path.exists(os.path.join(tmp_dir, "SSIS-123-fanart.jpg"))

    def test_skips_if_exists(self, tmp_dir):
        thumb = os.path.join(tmp_dir, "SSIS-123-thumb.jpg")
        fanart = os.path.join(tmp_dir, "SSIS-123-fanart.jpg")
        open(thumb, "w").close()
        open(fanart, "w").close()
        copy_as_fanart(tmp_dir, "SSIS-123")  # should not raise


class TestDeleteThumb:
    def test_deletes_when_not_keep(self, tmp_dir):
        thumb = os.path.join(tmp_dir, "SSIS-123-thumb.jpg")
        open(thumb, "w").close()
        delete_thumb(tmp_dir, "SSIS-123", keep_thumb=False)
        assert not os.path.exists(thumb)

    def test_keeps_when_keep(self, tmp_dir):
        thumb = os.path.join(tmp_dir, "SSIS-123-thumb.jpg")
        open(thumb, "w").close()
        delete_thumb(tmp_dir, "SSIS-123", keep_thumb=True)
        assert os.path.exists(thumb)


class TestPasteFileToFolder:
    def test_moves_file(self, tmp_dir):
        src_dir = os.path.join(tmp_dir, "src")
        dst_dir = os.path.join(tmp_dir, "dst")
        os.makedirs(src_dir)
        os.makedirs(dst_dir)
        src_file = os.path.join(src_dir, "SSIS-123.mp4")
        open(src_file, "w").close()
        config = AppConfig(soft_link=0)
        result = paste_file_to_folder(src_file, dst_dir, "SSIS-123",
                                      os.path.join(tmp_dir, "failed"), config)
        assert os.path.exists(os.path.join(dst_dir, "SSIS-123.mp4"))

    def test_symlink(self, tmp_dir):
        src_dir = os.path.join(tmp_dir, "src")
        dst_dir = os.path.join(tmp_dir, "dst")
        os.makedirs(src_dir)
        os.makedirs(dst_dir)
        src_file = os.path.join(src_dir, "SSIS-123.mp4")
        open(src_file, "w").close()
        config = AppConfig(soft_link=1)
        paste_file_to_folder(src_file, dst_dir, "SSIS-123",
                             os.path.join(tmp_dir, "failed"), config)
        link = os.path.join(dst_dir, "SSIS-123.mp4")
        assert os.path.islink(link)


class TestEnsureFailedFolder:
    def test_creates_when_enabled(self, tmp_dir):
        failed = os.path.join(tmp_dir, "failed")
        config = AppConfig(failed_file_move=1)
        ensure_failed_folder(failed, config)
        assert os.path.exists(failed)

    def test_skips_when_disabled(self, tmp_dir):
        failed = os.path.join(tmp_dir, "failed2")
        config = AppConfig(failed_file_move=0)
        ensure_failed_folder(failed, config)
        assert not os.path.exists(failed)


class TestCleanEmptyDirs:
    def test_removes_empty(self, tmp_dir):
        empty = os.path.join(tmp_dir, "empty_dir")
        os.makedirs(empty)
        clean_empty_dirs(tmp_dir)
        assert not os.path.exists(empty)

    def test_keeps_nonempty(self, tmp_dir):
        subdir = os.path.join(tmp_dir, "has_file")
        os.makedirs(subdir)
        open(os.path.join(subdir, "file.txt"), "w").close()
        clean_empty_dirs(tmp_dir)
        assert os.path.exists(subdir)


class TestResolveNamingRule:
    def test_basic(self):
        json_data = {
            "title": "Test", "number": "SSIS-123", "actor": "Alice",
            "studio": "S1", "publisher": "Will", "year": "2021",
            "outline": "", "runtime": "", "director": "",
            "release": "2021-05-01", "tag": [], "cover": "",
            "website": "", "series": "", "actor_photo": {},
            "naming_file": "number-title", "naming_media": "",
            "folder_name": "", "cover_small": "", "score": "",
            "imagecut": 1, "extrafanart": [], "source": "",
        }
        result = resolve_naming_rule(json_data)
        assert "SSIS-123" in result
        assert "Test" in result
