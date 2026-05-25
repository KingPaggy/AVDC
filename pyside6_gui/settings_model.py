"""
SettingsModel — PySide6 QML data binding layer for AppConfig.

Exposes all config.ini fields as Qt Properties with change notification,
enabling two-way QML binding. Load/save delegates to core._config.
"""
from __future__ import annotations

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


class SettingsModel(QObject):
    """QML-accessible config model. Each field is a Property with notify signal."""

    # Notify signals (one per config field)
    mainModeChanged = Signal(int)
    softLinkChanged = Signal(int)
    failedFileMoveChanged = Signal(int)
    showPosterChanged = Signal(int)
    websiteChanged = Signal(str)
    successOutputFolderChanged = Signal(str)
    failedOutputFolderChanged = Signal(str)
    proxyTypeChanged = Signal(str)
    proxyChanged = Signal(str)
    timeoutChanged = Signal(int)
    retryChanged = Signal(int)
    folderNameChanged = Signal(str)
    namingMediaChanged = Signal(str)
    namingFileChanged = Signal(str)
    updateCheckChanged = Signal(int)
    saveLogChanged = Signal(int)
    mediaTypeChanged = Signal(str)
    subTypeChanged = Signal(str)
    mediaPathChanged = Signal(str)
    literalsChanged = Signal(str)
    foldersChanged = Signal(str)
    stringChanged = Signal(str)
    switchDebugChanged = Signal(int)
    embyUrlChanged = Signal(str)
    apiKeyChanged = Signal(str)
    posterMarkChanged = Signal(int)
    thumbMarkChanged = Signal(int)
    markSizeChanged = Signal(int)
    markTypeChanged = Signal(str)
    markPosChanged = Signal(str)
    uncensoredPosterChanged = Signal(int)
    uncensoredPrefixChanged = Signal(str)
    nfoDownloadChanged = Signal(int)
    posterDownloadChanged = Signal(int)
    fanartDownloadChanged = Signal(int)
    thumbDownloadChanged = Signal(int)
    extrafanartDownloadChanged = Signal(int)
    extrafanartFolderChanged = Signal(str)
    baiduAppIdChanged = Signal(str)
    baiduApiKeyChanged = Signal(str)
    baiduSecretKeyChanged = Signal(str)

    # Status signals
    configLoaded = Signal()
    configSaved = Signal()
    errorOccurred = Signal(str)

    def __init__(self, config_path: str = ""):
        super().__init__()
        self._config_path = config_path or _find_config_file()
        self._defaults = self._load_defaults()
        self._fields: dict = dict(self._defaults)
        self.load()

    # ---- Property getter/setter pairs ----

    def _make_prop(name, signal):
        """Factory for creating getter/setter closures."""
        def getter(self):
            return self._fields.get(name)
        def setter(self, v):
            self._fields[name] = v
            getattr(self, signal).emit(v)
        return getter, setter

    # [common]
    _get_main_mode, _set_main_mode = _make_prop("main_mode", "mainModeChanged")
    mainMode = Property(int, _get_main_mode, _set_main_mode, notify=mainModeChanged)

    _get_soft_link, _set_soft_link = _make_prop("soft_link", "softLinkChanged")
    softLink = Property(int, _get_soft_link, _set_soft_link, notify=softLinkChanged)

    _get_ffm, _set_ffm = _make_prop("failed_file_move", "failedFileMoveChanged")
    failedFileMove = Property(int, _get_ffm, _set_ffm, notify=failedFileMoveChanged)

    _get_sp, _set_sp = _make_prop("show_poster", "showPosterChanged")
    showPoster = Property(int, _get_sp, _set_sp, notify=showPosterChanged)

    _get_ws, _set_ws = _make_prop("website", "websiteChanged")
    website = Property(str, _get_ws, _set_ws, notify=websiteChanged)

    _get_sof, _set_sof = _make_prop("success_output_folder", "successOutputFolderChanged")
    successOutputFolder = Property(str, _get_sof, _set_sof, notify=successOutputFolderChanged)

    _get_fof, _set_fof = _make_prop("failed_output_folder", "failedOutputFolderChanged")
    failedOutputFolder = Property(str, _get_fof, _set_fof, notify=failedOutputFolderChanged)

    # [proxy]
    _get_pt, _set_pt = _make_prop("proxy_type", "proxyTypeChanged")
    proxyType = Property(str, _get_pt, _set_pt, notify=proxyTypeChanged)

    _get_px, _set_px = _make_prop("proxy", "proxyChanged")
    proxy = Property(str, _get_px, _set_px, notify=proxyChanged)

    _get_to, _set_to = _make_prop("timeout", "timeoutChanged")
    timeout = Property(int, _get_to, _set_to, notify=timeoutChanged)

    _get_re, _set_re = _make_prop("retry", "retryChanged")
    retry = Property(int, _get_re, _set_re, notify=retryChanged)

    # [Name_Rule]
    _get_fn, _set_fn = _make_prop("folder_name", "folderNameChanged")
    folderName = Property(str, _get_fn, _set_fn, notify=folderNameChanged)

    _get_nm, _set_nm = _make_prop("naming_media", "namingMediaChanged")
    namingMedia = Property(str, _get_nm, _set_nm, notify=namingMediaChanged)

    _get_nf, _set_nf = _make_prop("naming_file", "namingFileChanged")
    namingFile = Property(str, _get_nf, _set_nf, notify=namingFileChanged)

    # [update]
    _get_uc, _set_uc = _make_prop("update_check", "updateCheckChanged")
    updateCheck = Property(int, _get_uc, _set_uc, notify=updateCheckChanged)

    # [log]
    _get_sl, _set_sl = _make_prop("save_log", "saveLogChanged")
    saveLog = Property(int, _get_sl, _set_sl, notify=saveLogChanged)

    # [media]
    _get_mt, _set_mt = _make_prop("media_type", "mediaTypeChanged")
    mediaType = Property(str, _get_mt, _set_mt, notify=mediaTypeChanged)

    _get_st, _set_st = _make_prop("sub_type", "subTypeChanged")
    subType = Property(str, _get_st, _set_st, notify=subTypeChanged)

    _get_mp, _set_mp = _make_prop("media_path", "mediaPathChanged")
    mediaPath = Property(str, _get_mp, _set_mp, notify=mediaPathChanged)

    # [escape]
    _get_li, _set_li = _make_prop("literals", "literalsChanged")
    literals = Property(str, _get_li, _set_li, notify=literalsChanged)

    _get_fo, _set_fo = _make_prop("folders", "foldersChanged")
    escapeFolders = Property(str, _get_fo, _set_fo, notify=foldersChanged)

    _get_es, _set_es = _make_prop("string", "stringChanged")
    escapeString = Property(str, _get_es, _set_es, notify=stringChanged)

    # [debug_mode]
    _get_sd, _set_sd = _make_prop("switch_debug", "switchDebugChanged")
    switchDebug = Property(int, _get_sd, _set_sd, notify=switchDebugChanged)

    # [emby]
    _get_eu, _set_eu = _make_prop("emby_url", "embyUrlChanged")
    embyUrl = Property(str, _get_eu, _set_eu, notify=embyUrlChanged)

    _get_ak, _set_ak = _make_prop("api_key", "apiKeyChanged")
    apiKey = Property(str, _get_ak, _set_ak, notify=apiKeyChanged)

    # [mark]
    _get_pm, _set_pm = _make_prop("poster_mark", "posterMarkChanged")
    posterMark = Property(int, _get_pm, _set_pm, notify=posterMarkChanged)

    _get_tm, _set_tm = _make_prop("thumb_mark", "thumbMarkChanged")
    thumbMark = Property(int, _get_tm, _set_tm, notify=thumbMarkChanged)

    _get_ms, _set_ms = _make_prop("mark_size", "markSizeChanged")
    markSize = Property(int, _get_ms, _set_ms, notify=markSizeChanged)

    _get_mty, _set_mty = _make_prop("mark_type", "markTypeChanged")
    markType = Property(str, _get_mty, _set_mty, notify=markTypeChanged)

    _get_mpo, _set_mpo = _make_prop("mark_pos", "markPosChanged")
    markPos = Property(str, _get_mpo, _set_mpo, notify=markPosChanged)

    # [uncensored]
    _get_up, _set_up = _make_prop("uncensored_poster", "uncensoredPosterChanged")
    uncensoredPoster = Property(int, _get_up, _set_up, notify=uncensoredPosterChanged)

    _get_upr, _set_upr = _make_prop("uncensored_prefix", "uncensoredPrefixChanged")
    uncensoredPrefix = Property(str, _get_upr, _set_upr, notify=uncensoredPrefixChanged)

    # [file_download]
    _get_nd, _set_nd = _make_prop("nfo_download", "nfoDownloadChanged")
    nfoDownload = Property(int, _get_nd, _set_nd, notify=nfoDownloadChanged)

    _get_pd, _set_pd = _make_prop("poster_download", "posterDownloadChanged")
    posterDownload = Property(int, _get_pd, _set_pd, notify=posterDownloadChanged)

    _get_fd, _set_fd = _make_prop("fanart_download", "fanartDownloadChanged")
    fanartDownload = Property(int, _get_fd, _set_fd, notify=fanartDownloadChanged)

    _get_td, _set_td = _make_prop("thumb_download", "thumbDownloadChanged")
    thumbDownload = Property(int, _get_td, _set_td, notify=thumbDownloadChanged)

    # [extrafanart]
    _get_ed, _set_ed = _make_prop("extrafanart_download", "extrafanartDownloadChanged")
    extrafanartDownload = Property(int, _get_ed, _set_ed, notify=extrafanartDownloadChanged)

    _get_ef, _set_ef = _make_prop("extrafanart_folder", "extrafanartFolderChanged")
    extrafanartFolder = Property(str, _get_ef, _set_ef, notify=extrafanartFolderChanged)

    # [baidu]
    _get_ba, _set_ba = _make_prop("baidu_app_id", "baiduAppIdChanged")
    baiduAppId = Property(str, _get_ba, _set_ba, notify=baiduAppIdChanged)

    _get_bk, _set_bk = _make_prop("baidu_api_key", "baiduApiKeyChanged")
    baiduApiKey = Property(str, _get_bk, _set_bk, notify=baiduApiKeyChanged)

    _get_bs, _set_bs = _make_prop("baidu_secret_key", "baiduSecretKeyChanged")
    baiduSecretKey = Property(str, _get_bs, _set_bs, notify=baiduSecretKeyChanged)

    # ---- Methods ----

    def _load_defaults(self) -> dict:
        return {
            "main_mode": 1, "soft_link": 0, "failed_file_move": 1, "show_poster": 0,
            "website": "all", "success_output_folder": "JAV_output",
            "failed_output_folder": "failed",
            "proxy_type": "no", "proxy": "", "timeout": 7, "retry": 3,
            "folder_name": "actor/number-title-release",
            "naming_media": "number-title", "naming_file": "number",
            "update_check": 0, "save_log": 0,
            "media_type": ".mp4|.avi|.rmvb|.wmv|.mov|.mkv",
            "sub_type": ".srt|.ass|.sub", "media_path": "",
            "literals": "", "folders": "failed,JAV_output", "string": "",
            "switch_debug": 0, "emby_url": "", "api_key": "",
            "poster_mark": 0, "thumb_mark": 0, "mark_size": 10,
            "mark_type": "", "mark_pos": "top_left",
            "uncensored_poster": 0, "uncensored_prefix": "",
            "nfo_download": 1, "poster_download": 1, "fanart_download": 1, "thumb_download": 1,
            "extrafanart_download": 0, "extrafanart_folder": "extrafanart",
            "baidu_app_id": "", "baidu_api_key": "", "baidu_secret_key": "",
        }

    @Slot()
    def load(self):
        """Load config from config.ini into all properties."""
        try:
            from core._config.config import AppConfig
            cfg = AppConfig.from_ini(self._config_path)
            self._fields.update({
                "main_mode": cfg.main_mode, "soft_link": cfg.soft_link,
                "failed_file_move": cfg.failed_file_move, "show_poster": cfg.show_poster,
                "website": cfg.website, "success_output_folder": cfg.success_output_folder,
                "failed_output_folder": cfg.failed_output_folder,
                "proxy_type": cfg.proxy_type, "proxy": cfg.proxy,
                "timeout": cfg.timeout, "retry": cfg.retry,
                "folder_name": cfg.folder_name, "naming_media": cfg.naming_media,
                "naming_file": cfg.naming_file,
                "update_check": cfg.update_check, "save_log": cfg.save_log,
                "media_type": cfg.media_type, "sub_type": cfg.sub_type,
                "media_path": cfg.media_path,
                "literals": cfg.literals, "folders": cfg.folders, "string": cfg.string,
                "switch_debug": cfg.switch_debug,
                "emby_url": cfg.emby_url, "api_key": cfg.api_key,
                "poster_mark": cfg.poster_mark, "thumb_mark": cfg.thumb_mark,
                "mark_size": cfg.mark_size, "mark_type": cfg.mark_type,
                "mark_pos": cfg.mark_pos,
                "uncensored_poster": cfg.uncensored_poster,
                "uncensored_prefix": cfg.uncensored_prefix,
                "nfo_download": cfg.nfo_download, "poster_download": cfg.poster_download,
                "fanart_download": cfg.fanart_download, "thumb_download": cfg.thumb_download,
                "extrafanart_download": cfg.extrafanart_download,
                "extrafanart_folder": cfg.extrafanart_folder,
                "baidu_app_id": cfg.baidu_app_id, "baidu_api_key": cfg.baidu_api_key,
                "baidu_secret_key": cfg.baidu_secret_key,
            })
            self.configLoaded.emit()
        except Exception as e:
            self.errorOccurred.emit(f"加载配置失败: {e}")

    @Slot()
    def save(self):
        """Write all properties to config.ini."""
        try:
            from core._config.config import AppConfig
            cfg = AppConfig(**self._fields)
            cfg.to_ini(self._config_path)
            self.configSaved.emit()
        except Exception as e:
            self.errorOccurred.emit(f"保存配置失败: {e}")

    @Slot()
    def resetToDefaults(self):
        """Reset all properties to default values."""
        self._fields = dict(self._defaults)
        # Emit all change signals so QML bindings update
        signal_map = self._signal_map()
        for name, value in self._fields.items():
            if name in signal_map:
                signal_map[name].emit(value)
        self.configLoaded.emit()

    def _signal_map(self) -> dict:
        return {
            "main_mode": self.mainModeChanged, "soft_link": self.softLinkChanged,
            "failed_file_move": self.failedFileMoveChanged,
            "show_poster": self.showPosterChanged,
            "website": self.websiteChanged,
            "success_output_folder": self.successOutputFolderChanged,
            "failed_output_folder": self.failedOutputFolderChanged,
            "proxy_type": self.proxyTypeChanged, "proxy": self.proxyChanged,
            "timeout": self.timeoutChanged, "retry": self.retryChanged,
            "folder_name": self.folderNameChanged,
            "naming_media": self.namingMediaChanged,
            "naming_file": self.namingFileChanged,
            "update_check": self.updateCheckChanged,
            "save_log": self.saveLogChanged,
            "media_type": self.mediaTypeChanged,
            "sub_type": self.subTypeChanged,
            "media_path": self.mediaPathChanged,
            "literals": self.literalsChanged,
            "folders": self.foldersChanged,
            "string": self.stringChanged,
            "switch_debug": self.switchDebugChanged,
            "emby_url": self.embyUrlChanged,
            "api_key": self.apiKeyChanged,
            "poster_mark": self.posterMarkChanged,
            "thumb_mark": self.thumbMarkChanged,
            "mark_size": self.markSizeChanged,
            "mark_type": self.markTypeChanged,
            "mark_pos": self.markPosChanged,
            "uncensored_poster": self.uncensoredPosterChanged,
            "uncensored_prefix": self.uncensoredPrefixChanged,
            "nfo_download": self.nfoDownloadChanged,
            "poster_download": self.posterDownloadChanged,
            "fanart_download": self.fanartDownloadChanged,
            "thumb_download": self.thumbDownloadChanged,
            "extrafanart_download": self.extrafanartDownloadChanged,
            "extrafanart_folder": self.extrafanartFolderChanged,
            "baidu_app_id": self.baiduAppIdChanged,
            "baidu_api_key": self.baiduApiKeyChanged,
            "baidu_secret_key": self.baiduSecretKeyChanged,
        }
