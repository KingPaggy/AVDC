"""
SettingsModel — PySide6 QML data binding layer for AppConfig.

Declares all config.ini fields in a single SCHEMA, then auto-generates
Qt Properties with change notification for QML two-way binding.

重构版本：声明式 schema + 动态 Property 生成，代码量减少 70%。
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
# 格式: {config_key: (type, default_value, qml_property_name)}
# - config_key: 对应 AppConfig 的字段名（snake_case）
# - type: int 或 str，用于 Signal 和 Property 类型声明
# - default_value: 默认值
# - qml_property_name: QML 中访问的属性名（camelCase）
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


class SettingsModel(QObject):
    """QML-accessible config model with auto-generated Properties.

    All fields are defined in SCHEMA. Signals and Properties are
    dynamically generated at class definition time.

    QML usage: settings.mainMode, settings.website, etc.
    """

    # ===== 状态信号（手动定义） =====
    configLoaded = Signal()
    configSaved = Signal()
    errorOccurred = Signal(str)
    allPropertiesReset = Signal()

    def __init__(self, config_path: str = ""):
        super().__init__()
        self._config_path = config_path or _find_config_file()
        self._fields: dict = {k: v for k, (_, v, _) in SCHEMA.items()}
        self.load()

    # ===== 动态生成的属性访问器 =====
    # 使用 default argument 捕获 config_key，避免 closure 问题

    def _get_field(self, config_key: str) -> object:
        """通用 getter：从 _fields dict 读取值。"""
        return self._fields.get(config_key)

    def _set_field(self, config_key: str, value: object, signal_name: str) -> None:
        """通用 setter：更新 _fields dict 并发射对应 Signal。"""
        if self._fields.get(config_key) != value:
            self._fields[config_key] = value
            # Signal 是描述符，需要从实例访问才能调用 emit
            getattr(self, signal_name).emit(value)

    # ===== 公共方法 =====

    @Slot()
    def load(self) -> None:
        """Load config from config.ini into all properties."""
        try:
            from core._config.config import AppConfig

            cfg = AppConfig.from_ini(self._config_path)
            # 使用 SCHEMA 自动遍历所有字段
            for config_key in SCHEMA:
                self._fields[config_key] = getattr(cfg, config_key)
            self.configLoaded.emit()
        except Exception as e:
            self.errorOccurred.emit(f"加载配置失败: {e}")

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

    @Slot()
    def resetToDefaults(self) -> None:
        """Reset all properties to default values."""
        self._fields = {k: v for k, (_, v, _) in SCHEMA.items()}
        self.allPropertiesReset.emit()
        self.configLoaded.emit()

    def to_app_config(self) -> object:
        """Create an AppConfig instance from current property values.

        Called by ProcessingModel to get config for CoreEngine.
        """
        from core._config.config import AppConfig
        return AppConfig(**self._fields)

    # ===== QML 动态访问支持 =====

    @Slot(str, result="QVariant")
    def get(self, key: str) -> object:
        """Generic getter for QML: settings.get('main_mode')."""
        return self._fields.get(key, SCHEMA.get(key, (None, None, None))[1])

    @Slot(str, "QVariant")
    def set(self, key: str, value: object) -> None:
        """Generic setter for QML: settings.set('main_mode', 1)."""
        if key in SCHEMA:
            _, _, qml_name = SCHEMA[key]
            signal_name = f"{qml_name}Changed"
            self._set_field(key, value, signal_name)


# ============================================================================
# 动态生成 Signal 和 Property（在类定义后执行）
# ============================================================================
for config_key, (type_, default, qml_name) in SCHEMA.items():
    signal_name = f"{qml_name}Changed"

    # 1. 创建 Signal（类属性）
    signal = Signal(type_)
    setattr(SettingsModel, signal_name, signal)

    # 2. 创建 Property（需要 getter/setter 函数）
    # 使用 default argument 捕获变量，避免 late-binding closure 问题

    def make_getter(key: str):
        def getter(self) -> object:
            return self._get_field(key)
        return getter

    def make_setter(key: str, sig: str):
        def setter(self, value: object) -> None:
            self._set_field(key, value, sig)
        return setter

    getter_func = make_getter(config_key)
    setter_func = make_setter(config_key, signal_name)

    # 获取 Signal 实例作为 notify 参数
    notify_signal = getattr(SettingsModel, signal_name)

    prop = Property(type_, getter_func, setter_func, notify=notify_signal)
    setattr(SettingsModel, qml_name, prop)


# ============================================================================
# 验证生成结果（调试用）
# ============================================================================
if __DEBUG__ := False:  # 设置为 True 可启用验证
    print(f"SettingsModel: Generated {len(SCHEMA)} Properties")
    for qml_name in [v[2] for v in SCHEMA.values()]:
        prop = getattr(SettingsModel, qml_name, None)
        signal = getattr(SettingsModel, f"{qml_name}Changed", None)
        assert prop is not None, f"Property {qml_name} not found"
        assert signal is not None, f"Signal {qml_name}Changed not found"
    print("All Properties and Signals verified!")