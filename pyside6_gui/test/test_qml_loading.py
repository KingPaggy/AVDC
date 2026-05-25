"""Tests for QML file loading — validates all .qml files can be parsed by the engine."""
import os
import sys
import glob
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PySide6.QtCore import QObject


class TestQMLLoading:
    """Test that QML files can be loaded by QQmlApplicationEngine."""

    def test_main_qml_loads(self, qml_engine):
        """main.qml should load successfully (at least one rootObject)."""
        qml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qml"))
        main_qml = os.path.join(qml_dir, "main.qml")
        qml_engine.load(main_qml)

        root_objects = qml_engine.rootObjects()
        assert len(root_objects) > 0, "main.qml failed to load — no root objects"

    def test_all_qml_files_parseable(self, qml_engine):
        """All .qml files in qml/ and qml/components/ should parse without import errors."""
        qml_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qml"))

        # Collect all .qml files except main.qml (tested separately)
        qml_files = glob.glob(os.path.join(qml_dir, "*.qml"))
        qml_files += glob.glob(os.path.join(qml_dir, "components", "*.qml"))
        qml_files = [f for f in qml_files if os.path.basename(f) != "main.qml"]

        errors = []
        for qml_file in sorted(qml_files):
            engine = qml_engine  # reuse engine with context properties
            engine.load(qml_file)
            if not engine.rootObjects():
                errors.append(os.path.basename(qml_file))
            # Clear for next load (create fresh engine)
            from PySide6.QtQml import QQmlApplicationEngine
            from PySide6.QtGui import QGuiApplication
            app = QGuiApplication.instance()
            engine = QQmlApplicationEngine()
            engine.rootContext().setContextProperty("Theme", {})  # minimal Theme
            from settings_model import SettingsModel
            import tempfile
            with tempfile.TemporaryDirectory() as tmp:
                config_path = os.path.join(tmp, "config.ini")
                with open(config_path, "w") as f:
                    f.write("[common]\nmain_mode = 1\nsoft_link = 0\nfailed_file_move = 1\nsuccess_output_folder = JAV_output\nfailed_output_folder = failed\nwebsite = all\n\n[proxy]\nproxy_type = no\nproxy =\ntimeout = 5\nretry = 3\n\n[Name_Rule]\nfolder_name = actor\nnaming_media = number\nnaming_file = number\n\n[update]\nupdate_check = 0\n\n[log]\nsave_log = 0\n\n[media]\nmedia_type = .mp4\nsub_type = .srt\nmedia_path =\n\n[escape]\nliterals =\nfolders = failed\nstring =\n\n[debug_mode]\nswitch_debug = 0\n\n[emby]\nemby_url =\napi_key =\n\n[mark]\nposter_mark = 0\nthumb_mark = 0\nmark_size = 10\nmark_type =\nmark_pos = top_left\n\n[uncensored]\nuncensored_poster = 0\nuncensored_prefix =\n\n[file_download]\nnfo_download = 1\nposter_download = 1\nfanart_download = 1\nthumb_download = 1\n\n[extrafanart]\nextrafanart_download = 0\nextrafanart_folder = extrafanart\n\n[baidu]\nbaidu_app_id =\nbaidu_api_key =\nbaidu_secret_key =\n")
                settings = SettingsModel(config_path=config_path)
                engine.rootContext().setContextProperty("settings", settings)
                engine.rootContext().setContextProperty("Theme", {})
                qml_engine = engine  # update for next iteration

        assert len(errors) == 0, f"Failed to load QML files: {', '.join(errors)}"


class TestQMLContextProperties:
    """Test that context properties are correctly configured."""

    def test_theme_context_has_expected_keys(self, qml_engine):
        """Theme context property should be a dict with expected keys."""
        theme = qml_engine.rootContext().contextProperty("Theme")
        assert isinstance(theme, dict), "Theme should be a dict"
        assert "textColor" in theme
        assert "accentColor" in theme
        assert "spacingSM" in theme
        assert "fontBody" in theme

    def test_settings_context_is_qobject(self, qml_engine):
        """Settings context property should be a QObject."""
        settings = qml_engine.rootContext().contextProperty("settings")
        assert isinstance(settings, QObject), "Settings should be a QObject"
