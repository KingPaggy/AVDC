"""
AppConfig — typed configuration relay between UI and business logic.

Business modules should use: from core._config.config import AppConfig
UI layer reads/writes config.ini through AppConfig, never directly.

This module has ZERO Qt dependencies.
"""

import os
from configparser import ConfigParser
from dataclasses import dataclass, field


def _find_config_file() -> str:
    """Locate config.ini in current or parent directory."""
    if os.path.exists("config.ini"):
        return "config.ini"
    if os.path.exists("../config.ini"):
        return "../config.ini"
    return "config.ini"


def _int_or(cfg: ConfigParser, section: str, key: str, default: int) -> int:
    """Read an int from config, fallback to default on error."""
    try:
        return int(cfg[section][key])
    except (KeyError, ValueError, TypeError):
        return default


def _str_or(cfg: ConfigParser, section: str, key: str, default: str) -> str:
    """Read a string from config, fallback to default on error."""
    try:
        return cfg[section][key]
    except (KeyError, TypeError):
        return default


@dataclass
class AppConfig:
    """All configuration fields, typed. Business code reads these, never self.Ui.*"""

    # [common]
    main_mode: int = 1
    soft_link: int = 0
    failed_file_move: int = 1
    show_poster: int = 0
    website: str = "all"
    success_output_folder: str = "JAV_output"
    failed_output_folder: str = "failed"

    # [proxy]
    proxy_type: str = "no"
    proxy: str = ""
    timeout: int = 5
    retry: int = 3

    # [Name_Rule]
    folder_name: str = "actor/number-title-release"
    naming_media: str = "number-title"
    naming_file: str = "number"

    # [update]
    update_check: int = 0

    # [log]
    save_log: int = 0

    # [media]
    media_type: str = ".mp4|.avi|.rmvb|.wmv|.mov|.mkv"
    sub_type: str = ".srt|.ass|.sub"
    media_path: str = ""

    # [escape]
    literals: str = ""
    folders: str = "failed,JAV_output"
    string: str = ""

    # [debug_mode]
    switch_debug: int = 0

    # [emby]
    emby_url: str = ""
    api_key: str = ""

    # [mark]
    poster_mark: int = 0
    thumb_mark: int = 0
    mark_size: int = 10
    mark_type: str = ""
    mark_pos: str = "top_left"

    # [uncensored]
    uncensored_poster: int = 0
    uncensored_prefix: str = ""

    # [file_download]
    nfo_download: int = 1
    poster_download: int = 1
    fanart_download: int = 1
    thumb_download: int = 1

    # [extrafanart]
    extrafanart_download: int = 0
    extrafanart_folder: str = "extrafanart"

    # [baidu] — new section for Baidu AI credentials
    baidu_app_id: str = ""
    baidu_api_key: str = ""
    baidu_secret_key: str = ""

    @classmethod
    def from_ini(cls, path: str = "") -> "AppConfig":
        """Load config from an ini file."""
        if not path:
            path = _find_config_file()
        cfg = ConfigParser()
        cfg.read(path, encoding="UTF-8")
        return cls(
            main_mode=_int_or(cfg, "common", "main_mode", 1),
            soft_link=_int_or(cfg, "common", "soft_link", 0),
            failed_file_move=_int_or(cfg, "common", "failed_file_move", 1),
            show_poster=_int_or(cfg, "common", "show_poster", 0),
            website=_str_or(cfg, "common", "website", "all"),
            success_output_folder=_str_or(cfg, "common", "success_output_folder", "JAV_output"),
            failed_output_folder=_str_or(cfg, "common", "failed_output_folder", "failed"),
            proxy_type=_str_or(cfg, "proxy", "type", "no"),
            proxy=_str_or(cfg, "proxy", "proxy", ""),
            timeout=_int_or(cfg, "proxy", "timeout", 5),
            retry=_int_or(cfg, "proxy", "retry", 3),
            folder_name=_str_or(cfg, "Name_Rule", "folder_name", "actor/number-title-release"),
            naming_media=_str_or(cfg, "Name_Rule", "naming_media", "number-title"),
            naming_file=_str_or(cfg, "Name_Rule", "naming_file", "number"),
            update_check=_int_or(cfg, "update", "update_check", 0),
            save_log=_int_or(cfg, "log", "save_log", 0),
            media_type=_str_or(cfg, "media", "media_type", ".mp4|.avi|.rmvb|.wmv|.mov|.mkv"),
            sub_type=_str_or(cfg, "media", "sub_type", ".srt|.ass|.sub"),
            media_path=_str_or(cfg, "media", "media_path", ""),
            literals=_str_or(cfg, "escape", "literals", ""),
            folders=_str_or(cfg, "escape", "folders", "failed,JAV_output"),
            string=_str_or(cfg, "escape", "string", ""),
            switch_debug=_int_or(cfg, "debug_mode", "switch", 0),
            emby_url=_str_or(cfg, "emby", "emby_url", ""),
            api_key=_str_or(cfg, "emby", "api_key", ""),
            poster_mark=_int_or(cfg, "mark", "poster_mark", 0),
            thumb_mark=_int_or(cfg, "mark", "thumb_mark", 0),
            mark_size=_int_or(cfg, "mark", "mark_size", 10),
            mark_type=_str_or(cfg, "mark", "mark_type", ""),
            mark_pos=_str_or(cfg, "mark", "mark_pos", "top_left"),
            uncensored_poster=_int_or(cfg, "uncensored", "uncensored_poster", 0),
            uncensored_prefix=_str_or(cfg, "uncensored", "uncensored_prefix", ""),
            nfo_download=_int_or(cfg, "file_download", "nfo", 1),
            poster_download=_int_or(cfg, "file_download", "poster", 1),
            fanart_download=_int_or(cfg, "file_download", "fanart", 1),
            thumb_download=_int_or(cfg, "file_download", "thumb", 1),
            extrafanart_download=_int_or(cfg, "extrafanart", "extrafanart_download", 0),
            extrafanart_folder=_str_or(cfg, "extrafanart", "extrafanart_folder", "extrafanart"),
            baidu_app_id=_str_or(cfg, "baidu", "app_id", ""),
            baidu_api_key=_str_or(cfg, "baidu", "api_key", ""),
            baidu_secret_key=_str_or(cfg, "baidu", "secret_key", ""),
        )

    def to_ini(self, path: str = "") -> None:
        """Write config to an ini file."""
        if not path:
            path = _find_config_file()
        cfg = ConfigParser()

        cfg["common"] = {
            "main_mode": str(self.main_mode),
            "soft_link": str(self.soft_link),
            "failed_file_move": str(self.failed_file_move),
            "show_poster": str(self.show_poster),
            "website": self.website,
            "success_output_folder": self.success_output_folder,
            "failed_output_folder": self.failed_output_folder,
        }
        cfg["proxy"] = {
            "type": self.proxy_type,
            "proxy": self.proxy,
            "timeout": str(self.timeout),
            "retry": str(self.retry),
        }
        cfg["Name_Rule"] = {
            "folder_name": self.folder_name,
            "naming_media": self.naming_media,
            "naming_file": self.naming_file,
        }
        cfg["update"] = {"update_check": str(self.update_check)}
        cfg["log"] = {"save_log": str(self.save_log)}
        cfg["media"] = {
            "media_type": self.media_type,
            "sub_type": self.sub_type,
            "media_path": self.media_path,
        }
        cfg["escape"] = {
            "literals": self.literals,
            "folders": self.folders,
            "string": self.string,
        }
        cfg["debug_mode"] = {"switch": str(self.switch_debug)}
        cfg["emby"] = {
            "emby_url": self.emby_url,
            "api_key": self.api_key,
        }
        cfg["mark"] = {
            "poster_mark": str(self.poster_mark),
            "thumb_mark": str(self.thumb_mark),
            "mark_size": str(self.mark_size),
            "mark_type": self.mark_type,
            "mark_pos": self.mark_pos,
        }
        cfg["uncensored"] = {
            "uncensored_prefix": self.uncensored_prefix,
            "uncensored_poster": str(self.uncensored_poster),
        }
        cfg["file_download"] = {
            "nfo": str(self.nfo_download),
            "poster": str(self.poster_download),
            "fanart": str(self.fanart_download),
            "thumb": str(self.thumb_download),
        }
        cfg["extrafanart"] = {
            "extrafanart_download": str(self.extrafanart_download),
            "extrafanart_folder": self.extrafanart_folder,
        }
        cfg["baidu"] = {
            "app_id": self.baidu_app_id,
            "api_key": self.baidu_api_key,
            "secret_key": self.baidu_secret_key,
        }

        with open(path, "w", encoding="UTF-8") as f:
            cfg.write(f)

    def get_proxies_dict(self) -> dict:
        """Return requests-compatible proxies dict based on proxy_type."""
        if self.proxy_type == "no" or not self.proxy:
            return {}
        scheme = "http" if self.proxy_type == "http" else "socks5"
        return {scheme: f"{scheme}://{self.proxy}"}

    # Section-to-field mapping for dotted access (e.g. "proxy.type" -> "proxy_type")
    _SECTION_FIELDS: dict[str, dict[str, str]] = field(default_factory=lambda: {
        "common": {
            "main_mode": "main_mode", "soft_link": "soft_link",
            "failed_file_move": "failed_file_move", "show_poster": "show_poster",
            "website": "website", "success_output_folder": "success_output_folder",
            "failed_output_folder": "failed_output_folder",
        },
        "proxy": {
            "type": "proxy_type", "proxy": "proxy",
            "timeout": "timeout", "retry": "retry",
        },
        "Name_Rule": {
            "folder_name": "folder_name", "naming_media": "naming_media",
            "naming_file": "naming_file",
        },
        "update": {"update_check": "update_check"},
        "log": {"save_log": "save_log"},
        "media": {
            "media_type": "media_type", "sub_type": "sub_type", "media_path": "media_path",
        },
        "escape": {
            "literals": "literals", "folders": "folders", "string": "string",
        },
        "debug_mode": {"switch": "switch_debug"},
        "emby": {"emby_url": "emby_url", "api_key": "api_key"},
        "mark": {
            "poster_mark": "poster_mark", "thumb_mark": "thumb_mark",
            "mark_size": "mark_size", "mark_type": "mark_type", "mark_pos": "mark_pos",
        },
        "uncensored": {
            "uncensored_prefix": "uncensored_prefix", "uncensored_poster": "uncensored_poster",
        },
        "file_download": {
            "nfo": "nfo_download", "poster": "poster_download",
            "fanart": "fanart_download", "thumb": "thumb_download",
        },
        "extrafanart": {
            "extrafanart_download": "extrafanart_download",
            "extrafanart_folder": "extrafanart_folder",
        },
        "baidu": {
            "app_id": "baidu_app_id", "api_key": "baidu_api_key",
            "secret_key": "baidu_secret_key",
        },
    })

    def _resolve_field(self, dotted: str) -> str | None:
        """Resolve 'section.key' or 'field' to the dataclass attribute name."""
        if "." in dotted:
            section, key = dotted.split(".", 1)
            return self._SECTION_FIELDS.get(section, {}).get(key)
        return dotted if hasattr(self, dotted) else None

    def get_field(self, dotted: str) -> str | None:
        """Get config value by dotted name (e.g. 'proxy.type') or field name."""
        field_name = self._resolve_field(dotted)
        if field_name and hasattr(self, field_name):
            return str(getattr(self, field_name))
        return None

    def set_field(self, dotted: str, value: str) -> bool:
        """Set config value by dotted name, with type coercion. Returns True if successful."""
        field_name = self._resolve_field(dotted)
        if not field_name or not hasattr(self, field_name):
            return False
        current = getattr(self, field_name)
        if isinstance(current, int):
            try:
                value = str(int(value))
            except ValueError:
                return False
        setattr(self, field_name, value)
        return True

    def all_fields(self) -> list[tuple[str, str, str]]:
        """Return list of (section, key, value) for all config fields."""
        result = []
        for section, fields in self._SECTION_FIELDS.items():
            for key, field_name in fields.items():
                if hasattr(self, field_name):
                    result.append((section, key, str(getattr(self, field_name))))
        return result
