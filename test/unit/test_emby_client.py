"""Tests for Function/emby_client.py"""
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

import pytest

from core._services.emby_client import (
    get_actor_list,
    list_actors,
    find_and_upload_pictures,
    upload_actor_photo,
    _normalize_url,
)


class TestNormalizeUrl:
    def test_replaces_fullwidth_colon(self):
        assert _normalize_url("localhost：8096") == "localhost:8096"

    def test_noop_for_normal_url(self):
        assert _normalize_url("localhost:8096") == "localhost:8096"


class TestGetActorList:
    def test_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"TotalRecordCount": 2, "Items": []}
        with patch("core._services.emby_client.requests.get", return_value=mock_resp):
            result = get_actor_list("localhost:8096", "testkey")
        assert result["TotalRecordCount"] == 2

    def test_error_returns_empty(self):
        with patch("core._services.emby_client.requests.get", side_effect=Exception("fail")):
            result = get_actor_list("localhost:8096", "testkey")
        assert result["TotalRecordCount"] == 0


class TestListActors:
    def _mock_actors(self):
        return {
            "TotalRecordCount": 3,
            "Items": [
                {"Name": "Alice", "ImageTags": {}},
                {"Name": "Bob", "ImageTags": {"Primary": "abc"}},
                {"Name": "Charlie", "ImageTags": {}},
            ],
        }

    def test_list_all(self):
        with patch("core._services.emby_client.get_actor_list", return_value=self._mock_actors()):
            result = list_actors("localhost:8096", "key", mode=3)
        assert len(result) == 3

    def test_list_without_avatar(self):
        with patch("core._services.emby_client.get_actor_list", return_value=self._mock_actors()):
            result = list_actors("localhost:8096", "key", mode=1)
        # Alice and Charlie have no avatar
        assert len(result) == 2

    def test_list_with_avatar(self):
        with patch("core._services.emby_client.get_actor_list", return_value=self._mock_actors()):
            result = list_actors("localhost:8096", "key", mode=2)
        # Only Bob has avatar
        assert len(result) == 1

    def test_empty_response(self):
        with patch("core._services.emby_client.get_actor_list", return_value={"TotalRecordCount": 0}):
            result = list_actors("localhost:8096", "key", mode=3)
        assert result == []


class TestFindAndUploadPictures:
    def test_uploads_when_mode_1(self, tmp_dir):
        # Setup Actor directory with a profile picture
        actor_dir = os.path.join(tmp_dir, "Actor")
        os.makedirs(actor_dir)
        pic_path = os.path.join(actor_dir, "Alice.jpg")
        with open(pic_path, "wb") as f:
            f.write(b"fake-image")

        actor_list = {
            "TotalRecordCount": 1,
            "Items": [{"Name": "Alice", "Id": "123", "ImageTags": {}}],
        }

        with patch("core._services.emby_client.get_actor_list", return_value=actor_list):
            with patch("core._services.emby_client.upload_actor_photo") as mock_upload:
                find_and_upload_pictures(
                    "localhost:8096", "key", actor_dir=actor_dir, mode=1,
                )
                mock_upload.assert_called_once()
                # Verify pic_path is correct
                call_args = mock_upload.call_args
                assert call_args[0][3] == pic_path

    def test_lists_only_when_mode_2(self, tmp_dir):
        actor_dir = os.path.join(tmp_dir, "Actor")
        os.makedirs(actor_dir)
        pic_path = os.path.join(actor_dir, "Alice.jpg")
        with open(pic_path, "wb") as f:
            f.write(b"fake-image")

        actor_list = {
            "TotalRecordCount": 1,
            "Items": [{"Name": "Alice", "Id": "123", "ImageTags": {}}],
        }

        with patch("core._services.emby_client.get_actor_list", return_value=actor_list):
            with patch("core._services.emby_client.upload_actor_photo") as mock_upload:
                find_and_upload_pictures(
                    "localhost:8096", "key", actor_dir=actor_dir, mode=2,
                )
                mock_upload.assert_not_called()

    def test_skips_when_actor_dir_missing(self, tmp_dir):
        non_existent = os.path.join(tmp_dir, "NoActor")
        with patch("core._services.emby_client.get_actor_list") as mock_get:
            find_and_upload_pictures("localhost:8096", "key", actor_dir=non_existent, mode=1)
            mock_get.assert_not_called()

    def test_aliases_match(self, tmp_dir):
        """Should match by alias name in parentheses."""
        actor_dir = os.path.join(tmp_dir, "Actor")
        os.makedirs(actor_dir)
        # Actor name is "Alice(Mary)" but picture is "Alice.jpg"
        pic_path = os.path.join(actor_dir, "Alice.jpg")
        with open(pic_path, "wb") as f:
            f.write(b"fake-image")

        actor_list = {
            "TotalRecordCount": 1,
            "Items": [{"Name": "Alice(Mary)", "Id": "123", "ImageTags": {}}],
        }

        with patch("core._services.emby_client.get_actor_list", return_value=actor_list):
            with patch("core._services.emby_client.upload_actor_photo") as mock_upload:
                find_and_upload_pictures(
                    "localhost:8096", "key", actor_dir=actor_dir, mode=1,
                )
                mock_upload.assert_called_once()


class TestUploadActorPhoto:
    def test_calls_post_with_correct_url(self, tmp_dir):
        pic_path = os.path.join(tmp_dir, "test.jpg")
        with open(pic_path, "wb") as f:
            f.write(b"fake-img")
        with patch("core._services.emby_client.requests.post") as mock_post:
            upload_actor_photo(
                "localhost:8096", "key123",
                {"Id": "456", "Name": "Alice"},
                pic_path,
            )
        _, kwargs = mock_post.call_args
        assert "456" in kwargs["url"]
        assert "key123" in kwargs["url"]
        assert kwargs["headers"]["Content-Type"] == "image/png"
