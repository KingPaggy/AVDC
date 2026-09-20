"""
SettingsModel — PySide6 QML data binding layer for AppConfig.

Declares all config.ini fields in a single SCHEMA, then auto-generates
Qt Properties with change notification for QML two-way binding.

重构版本：使用类工厂在类创建时注入 Property，确保 Qt meta-object 系统
能正确注册所有属性，QML 可正常访问。
"""

import os
from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot


def _find_config_file() -> str:
    """Locate config.ini, searching from pyside6_gui/ upward."""
    candidates = [
        Path(__file__).resolve().parents[1] / "config.ini",
        Path.cwd() / "config.ini",
        Path.cwd().parent / "config.ini",
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[-1])


# ============================================================================
# 声明式配置 Schema
# ============================================================================
SCHEMA: dict[str, tuple[type, object, str]] = {
    # [common]
    "main_mode": (int, 1, "mainMode"),
    "soft_link": (int, 0, "softLink"),
    "failed_file_move": (int, 1, "failedFileMove"),
    "show_poster": (int, 0, "showPoster"),
    "website": (str, "all", "website"),
    "success_output_folder": (str, "JAV_output", "successOutputFolder"),
    "failed_output_folder": (str, "failed", "failedOutputFolder"),
    # [proxy]
    "proxy_type": (str, "no", "proxyType"),
    "proxy": (str, "", "proxy"),
    "timeout": (int, 7, "timeout"),
    "retry": (int, 3, "retry"),
    # [Name_Rule]
    "folder_name": (str, "actor/number-title-release", "folderName"),
    "naming_media": (str, "number-title", "namingMedia"),
    "naming_file": (str, "number", "namingFile"),
    # [update]
    "update_check": (int, 0, "updateCheck"),
    # [log]
    "save_log": (int, 0, "saveLog"),
    # [media]
    "media_type": (str, ".mp4|.avi|.rmvb|.wmv|.mov|.mkv", "mediaType"),
    "sub_type": (str, ".srt|.ass|.sub", "subType"),
    "media_path": (str, "", "mediaPath"),
    # [escape]
    "literals": (str, "", "literals"),
    "folders": (str, "failed,JAV_output", "escapeFolders"),
    "string": (str, "", "escapeString"),
    # [debug_mode]
    "switch_debug": (int, 0, "switchDebug"),
    # [emby]
    "emby_url": (str, "", "embyUrl"),
    "api_key": (str, "", "apiKey"),
    # [mark]
    "poster_mark": (int, 0, "posterMark"),
    "thumb_mark": (int, 0, "thumbMark"),
    "mark_size": (int, 10, "markSize"),
    "mark_type": (str, "", "markType"),
    "mark_pos": (str, "top_left", "markPos"),
    # [uncensored]
    "uncensored_poster": (int, 0, "uncensoredPoster"),
    "uncensored_prefix": (str, "", "uncensoredPrefix"),
    # [file_download]
    "nfo_download": (int, 1, "nfoDownload"),
    "poster_download": (int, 1, "posterDownload"),
    "fanart_download": (int, 1, "fanartDownload"),
    "thumb_download": (int, 1, "thumbDownload"),
    # [extrafanart]
    "extrafanart_download": (int, 0, "extrafanartDownload"),
    "extrafanart_folder": (str, "extrafanart", "extrafanartFolder"),
    # [baidu]
    "baidu_app_id": (str, "", "baiduAppId"),
    "baidu_api_key": (str, "", "baiduApiKey"),
    "baidu_secret_key": (str, "", "baiduSecretKey"),
}


# ============================================================================
# 类工厂：在类创建时注入 Signal + Property，确保 meta-object 注册
# ============================================================================
def _create_settings_model_class() -> type:
    """Build the SettingsModel class with all Properties in the namespace."""

    # 1. 基础 namespace
    namespace: dict = {
        '__module__': __name__,
        '__qualname__': 'SettingsModel',
        '__doc__': 'QML-accessible config model with auto-generated Properties.',
        # 静态信号
        'configLoaded': Signal(),
        'configSaved': Signal(),
        'errorOccurred': Signal(str),
        'allPropertiesReset': Signal(),
    }

    # 2. 为每个 SCHEMA 字段创建 Signal + Property
    for config_key, (type_, default, qml_name) in SCHEMA.items():
        signal_name = f"{qml_name}Changed"
        namespace[signal_name] = Signal(type_)

        # getter/setter 通过闭包捕获 config_key
        def make_getter(key: str):
            def getter(self) -> object:
                return self._fields.get(key)
            return getter

        def make_setter(key: str, sig: str):
            def setter(self, value: object) -> None:
                if self._fields.get(key) != value:
                    self._fields[key] = value
                    getattr(self, sig).emit(value)
            return setter

        getter = make_getter(config_key)
        setter = make_setter(config_key, signal_name)
        prop = Property(type_, getter, setter, notify=namespace[signal_name])
        namespace[qml_name] = prop

    # 3. 实例方法
    def __init__(self, config_path: str = ""):
        QObject.__init__(self)
        self._config_path = config_path or _find_config_file()
        self._fields: dict = {k: v for k, (_, v, _) in SCHEMA.items()}
        self.load()

    namespace['__init__'] = __init__

    def _get_field(self, config_key: str) -> object:
        return self._fields.get(config_key)

    def _set_field(self, config_key: str, value: object, signal_name: str) -> None:
        if self._fields.get(config_key) != value:
            self._fields[config_key] = value
            getattr(self, signal_name).emit(value)

    namespace['_get_field'] = _get_field
    namespace['_set_field'] = _set_field

    @Slot()
    def load(self) -> None:
        """Load config from config.ini into all properties."""
        try:
            from core._config.config import AppConfig
            cfg = AppConfig.from_ini(self._config_path)
            for config_key in SCHEMA:
                self._fields[config_key] = getattr(cfg, config_key)
            self.configLoaded.emit()
        except Exception as e:
            self.errorOccurred.emit(f"加载配置失败: {e}")

    namespace['load'] = load

    @Slot()
    def save(self) -> None:
        """Write all properties to config.ini."""
        try:
            from core._config.config import AppConfig
            cfg = AppConfig(**self._fields)
            cfg.to_ini(self._config_path)
            self.configSaved.emit()
        except Exception as e:
            self.errorOccurred.emit(f"保存配置失败: {e}")

    namespace['save'] = save

    @Slot()
    def resetToDefaults(self) -> None:
        """Reset all properties to default values."""
        self._fields = {k: v for k, (_, v, _) in SCHEMA.items()}
        self.allPropertiesReset.emit()
        self.configLoaded.emit()

    namespace['resetToDefaults'] = resetToDefaults

    def to_app_config(self) -> object:
        """Create an AppConfig instance from current property values."""
        from core._config.config import AppConfig
        return AppConfig(**self._fields)

    namespace['to_app_config'] = to_app_config

    @Slot(str, result="QVariant")
    def get(self, key: str) -> object:
        """Generic getter for QML: settings.get('main_mode')."""
        return self._fields.get(key, SCHEMA.get(key, (None, None, None))[1])

    namespace['get'] = get

    @Slot(str, "QVariant")
    def set(self, key: str, value: object) -> None:
        """Generic setter for QML: settings.set('main_mode', 1)."""
        if key in SCHEMA:
            _, _, qml_name = SCHEMA[key]
            signal_name = f"{qml_name}Changed"
            self._set_field(key, value, signal_name)

    namespace['set'] = set

    # 4. 创建类
    return type('SettingsModel', (QObject,), namespace)


SettingsModel = _create_settings_model_class()
