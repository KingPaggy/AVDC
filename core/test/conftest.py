"""
Shared test fixtures for AVDC test suite.
"""
import os
import tempfile
import pytest


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory that is cleaned up after each test."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def tmp_log_dir(tmp_dir):
    """Provide a temporary Log directory."""
    log_dir = os.path.join(tmp_dir, "Log")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


@pytest.fixture
def tmp_config_ini(tmp_dir):
    """Provide a temporary config.ini path with default content."""
    config_path = os.path.join(tmp_dir, "config.ini")
    # Write a minimal valid config.ini
    content = """\
[common]
main_mode = 1
soft_link = 0
failed_file_move = 1
success_output_folder = JAV_output
failed_output_folder = failed
website = all

[proxy]
type = no
proxy =
timeout = 5
retry = 3

[Name_Rule]
folder_name = actor/number
naming_media = number-title
naming_file = number

[update]
update_check = 0

[log]
save_log = 0

[media]
media_type = .mp4|.avi|.rmvb|.wmv|.mov|.mkv
sub_type = .srt|.ass|.sub
media_path =

[escape]
literals =
folders = failed,JAV_output
string =

[debug_mode]
switch = 0

[emby]
emby_url =
api_key =

[mark]
poster_mark = 0
thumb_mark = 0
mark_size = 10
mark_type =
mark_pos = top_left

[uncensored]
uncensored_poster = 0
uncensored_prefix =

[file_download]
nfo = 1
poster = 1
fanart = 1
thumb = 1

[extrafanart]
extrafanart_download = 0
extrafanart_folder = extrafanart

[baidu]
app_id =
api_key =
secret_key =
"""
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    return config_path
