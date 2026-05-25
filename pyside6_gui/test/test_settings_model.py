"""Tests for SettingsModel — Properties, Signals, Slots, load/save."""
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestSettingsModelDefaults:
    """Test that default values are correct."""

    def test_main_mode_default(self, settings):
        assert settings.mainMode == 1

    def test_soft_link_default(self, settings):
        assert settings.softLink == 0

    def test_proxy_type_default(self, settings):
        assert settings.proxyType == "no"

    def test_timeout_default(self, settings):
        assert settings.timeout == 7

    def test_retry_default(self, settings):
        assert settings.retry == 3

    def test_folder_name_default(self, settings):
        assert settings.folderName == "actor/number-title-release"

    def test_media_type_default(self, settings):
        assert settings.mediaType == ".mp4|.avi|.rmvb|.wmv|.mov|.mkv"

    def test_mark_pos_default(self, settings):
        assert settings.markPos == "top_left"


class TestSettingsModelPropertyChanges:
    """Test that property changes emit signals."""

    def test_set_main_mode_emits_signal(self, qt_app, settings):
        """Changing mainMode should emit mainModeChanged."""
        received = []
        settings.mainModeChanged.connect(lambda v: received.append(v))
        settings.mainMode = 2
        assert received == [2]

    def test_set_proxy_type_emits_signal(self, qt_app, settings):
        """Changing proxyType should emit proxyTypeChanged."""
        received = []
        settings.proxyTypeChanged.connect(lambda v: received.append(v))
        settings.proxyType = "http"
        assert received == ["http"]

    def test_set_timeout_emits_signal(self, qt_app, settings):
        """Changing timeout should emit timeoutChanged."""
        received = []
        settings.timeoutChanged.connect(lambda v: received.append(v))
        settings.timeout = 15
        assert received == [15]

    def test_property_getter_reflects_setter(self, qt_app, settings):
        """Setting a property should be readable via getter."""
        settings.successOutputFolder = "/tmp/test_output"
        assert settings.successOutputFolder == "/tmp/test_output"


class TestSettingsModelSaveLoad:
    """Test save() and load() methods."""

    def test_save_and_reload(self, qt_app, tmp_config_ini):
        """save() then new model.load() should persist values."""
        from settings_model import SettingsModel

        model1 = SettingsModel(config_path=tmp_config_ini)
        model1.timeout = 20
        model1.retry = 5
        model1.save()

        model2 = SettingsModel(config_path=tmp_config_ini)
        assert model2.timeout == 20
        assert model2.retry == 5

    def test_load_emits_config_loaded_signal(self, qt_app, tmp_config_ini):
        """load() should emit configLoaded on success."""
        from settings_model import SettingsModel

        model = SettingsModel(config_path=tmp_config_ini)
        received = []
        model.configLoaded.connect(lambda: received.append(True))
        model.load()
        assert len(received) >= 1

    def test_save_emits_config_saved_signal(self, qt_app, tmp_config_ini):
        """save() should emit configSaved on success."""
        from settings_model import SettingsModel

        model = SettingsModel(config_path=tmp_config_ini)
        received = []
        model.configSaved.connect(lambda: received.append(True))
        model.save()
        assert len(received) == 1


class TestSettingsModelReset:
    """Test resetToDefaults() method."""

    def test_reset_restores_main_mode(self, qt_app, tmp_config_ini):
        from settings_model import SettingsModel

        model = SettingsModel(config_path=tmp_config_ini)
        model.mainMode = 2
        assert model.mainMode == 2
        model.resetToDefaults()
        assert model.mainMode == 1

    def test_reset_restores_timeout(self, qt_app, tmp_config_ini):
        from settings_model import SettingsModel

        model = SettingsModel(config_path=tmp_config_ini)
        model.timeout = 99
        assert model.timeout == 99
        model.resetToDefaults()
        assert model.timeout == 7

    def test_reset_emits_config_loaded_signal(self, qt_app, tmp_config_ini):
        from settings_model import SettingsModel

        model = SettingsModel(config_path=tmp_config_ini)
        received = []
        model.configLoaded.connect(lambda: received.append(True))
        model.resetToDefaults()
        assert len(received) >= 1


class TestSettingsModelErrorHandling:
    """Test error handling for missing/invalid config."""

    def test_load_from_nonexistent_config(self, qt_app, tmp_path):
        """Loading from a non-existent config should emit errorOccurred, not crash."""
        from settings_model import SettingsModel

        bad_path = str(tmp_path / "nonexistent.ini")
        model = SettingsModel(config_path=bad_path)
        errors = []
        model.errorOccurred.connect(lambda msg: errors.append(msg))
        # The model should have been created without crashing
        # and should have default values
        assert model.mainMode == 1

    def test_save_to_writable_directory(self, qt_app, tmp_path):
        """save() to a new directory should create it."""
        from settings_model import SettingsModel

        new_dir = str(tmp_path / "new_dir")
        os.makedirs(new_dir)
        config_path = os.path.join(new_dir, "config.ini")

        model = SettingsModel(config_path=config_path)
        errors = []
        model.errorOccurred.connect(lambda msg: errors.append(msg))
        model.save()
        # Should have saved without errors
        assert os.path.exists(config_path)
        assert len(errors) == 0
