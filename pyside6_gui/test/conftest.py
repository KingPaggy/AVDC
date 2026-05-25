"""Shared fixtures for PySide6 + QML test suite.

NOTE: QT_QPA_PLATFORM must be set before Qt initializes.
"""
import os
import tempfile

# Set offscreen mode BEFORE any Qt imports
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine


@pytest.fixture
def qt_app():
    """Provide a QApplication instance (shared across tests)."""
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])
    yield app


@pytest.fixture
def tmp_config_ini(tmp_path):
    """Provide a temporary config.ini path with default content."""
    config_path = str(tmp_path / "config.ini")
    content = """\
[common]
main_mode = 1
soft_link = 0
failed_file_move = 1
show_poster = 0
success_output_folder = JAV_output
failed_output_folder = failed
website = all

[proxy]
proxy_type = no
proxy =
timeout = 7
retry = 3

[Name_Rule]
folder_name = actor/number-title-release
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
switch_debug = 0

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
nfo_download = 1
poster_download = 1
fanart_download = 1
thumb_download = 1

[extrafanart]
extrafanart_download = 0
extrafanart_folder = extrafanart

[baidu]
baidu_app_id =
baidu_api_key =
baidu_secret_key =
"""
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
    return config_path


@pytest.fixture
def settings(qt_app, tmp_config_ini):
    """Provide a SettingsModel instance backed by a temporary config."""
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from settings_model import SettingsModel
    model = SettingsModel(config_path=tmp_config_ini)
    yield model


@pytest.fixture
def qml_engine(qt_app):
    """Provide a QQmlApplicationEngine with Theme + settings context properties."""
    import sys
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from main import THEME
    from settings_model import SettingsModel

    engine = QQmlApplicationEngine()

    # Create a settings model with a temp config
    with tempfile.TemporaryDirectory() as tmp:
        config_path = os.path.join(tmp, "config.ini")
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("[common]\nmain_mode = 1\nsoft_link = 0\nfailed_file_move = 1\nsuccess_output_folder = JAV_output\nfailed_output_folder = failed\nwebsite = all\n\n[proxy]\nproxy_type = no\nproxy =\ntimeout = 7\nretry = 3\n\n[Name_Rule]\nfolder_name = actor/number-title-release\nnaming_media = number-title\nnaming_file = number\n\n[update]\nupdate_check = 0\n\n[log]\nsave_log = 0\n\n[media]\nmedia_type = .mp4\nsub_type = .srt\nmedia_path =\n\n[escape]\nliterals =\nfolders = failed,JAV_output\nstring =\n\n[debug_mode]\nswitch_debug = 0\n\n[emby]\nemby_url =\napi_key =\n\n[mark]\nposter_mark = 0\nthumb_mark = 0\nmark_size = 10\nmark_type =\nmark_pos = top_left\n\n[uncensored]\nuncensored_poster = 0\nuncensored_prefix =\n\n[file_download]\nnfo_download = 1\nposter_download = 1\nfanart_download = 1\nthumb_download = 1\n\n[extrafanart]\nextrafanart_download = 0\nextrafanart_folder = extrafanart\n\n[baidu]\nbaidu_app_id =\nbaidu_api_key =\nbaidu_secret_key =\n")
        settings = SettingsModel(config_path=config_path)
        engine.rootContext().setContextProperty("settings", settings)
        engine.rootContext().setContextProperty("Theme", THEME)
        yield engine
