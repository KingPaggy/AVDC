#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable, Dict, Any, Optional

from core.events import EventType
from core.event_bus import EventBus
from core.settings_provider import SettingsProvider
from core.process_result import ProcessResult


@dataclass
class FileProcessDependencies:
    """Legacy callback bundle. DEPRECATED — use EventBus + SettingsProvider instead."""

    log: Callable[[str], None]
    debug: Callable[[Dict[str, Any]], None]
    get_json_data: Callable[[int, str, Any, str], Dict[str, Any]]
    create_folder: Callable[[str, Dict[str, Any], Any], str]
    get_part: Callable[[str, str], str]
    get_naming_rule: Callable[[Dict[str, Any]], str]
    move_failed_folder: Callable[[str, str], None]
    thumb_download: Callable[[Dict[str, Any], str, str, Any, str, str], None]
    small_cover_download: Callable[[str, str, Dict[str, Any], Any, str, str], str]
    cut_image: Callable[[int, str, str], None]
    fix_size: Callable[[str, str], None]
    copy_fanart: Callable[[str, str], None]
    delete_thumb: Callable[[str, str], None]
    paste_file: Callable[[str, str, str, str], bool]
    print_files: Callable[[str, str, int, int, Dict[str, Any], str, str], None]
    extrafanart_download: Callable[[Dict[str, Any], str, Any, str, str], None]
    add_mark: Callable[[str, str, int, int, int, Any], None]
    add_label_info: Callable[[Dict[str, Any]], None]
    register_result: Callable[[int, int, Dict[str, Any]], None]
    is_debug_enabled: Callable[[], bool]
    is_program_mode_move: Callable[[], bool]
    is_show_small_cover: Callable[[], bool]
    is_copy_fanart_enabled: Callable[[], bool]
    is_print_enabled: Callable[[], bool]
    is_extrafanart_enabled: Callable[[], bool]
    is_restore_imagecut_enabled: Callable[[], bool]


class _LegacySettingsAdapter(SettingsProvider):
    """Wrap old FileProcessDependencies callables as a SettingsProvider."""

    def __init__(self, deps: FileProcessDependencies):
        self._deps = deps

    def is_debug_enabled(self) -> bool:
        return self._deps.is_debug_enabled()

    def is_program_mode_move(self) -> bool:
        return self._deps.is_program_mode_move()

    def should_download_thumb(self) -> bool:
        return self._deps.is_show_small_cover()

    def should_download_poster(self) -> bool:
        return self._deps.is_show_small_cover()

    def should_download_fanart(self) -> bool:
        return True

    def should_download_nfo(self) -> bool:
        return self._deps.is_print_enabled()

    def should_copy_fanart(self) -> bool:
        return self._deps.is_copy_fanart_enabled()

    def should_restore_imagecut(self) -> bool:
        return self._deps.is_restore_imagecut_enabled()

    def is_extrafanart_enabled(self) -> bool:
        return self._deps.is_extrafanart_enabled()

    def is_print_enabled(self) -> bool:
        return self._deps.is_print_enabled()

    def get_mark_config(self) -> dict:
        return {}


class _LegacyEventBusAdapter(EventBus):
    """Wrap FileProcessDependencies callbacks as an EventBus."""

    def __init__(self, deps: FileProcessDependencies, count_claw: int, count: int):
        super().__init__()
        self._deps = deps
        self._count_claw = count_claw
        self._count = count

        # Register handlers that forward to legacy callbacks
        self.on(EventType.LOG_INFO, lambda e: deps.log(e.message))
        self.on(EventType.LOG_ERROR, lambda e: deps.log(e.message))
        self.on(EventType.SCRAPE_SUCCESS, lambda e: deps.register_result(
            e.count_claw, e.count, e.json_data
        ))
        self.on(EventType.SCRAPE_FAILED, lambda e: deps.move_failed_folder(
            e.filepath, e.failed_dir
        ))


class FileProcessingService:
    """Handle one movie file end-to-end without knowing about Qt widgets."""

    def process(
        self,
        *,
        filepath: str,
        number: str,
        mode: int,
        count_claw: int,
        count: int,
        config: Any,
        movie_path: str,
        failed_folder: str,
        success_folder: str,
        appoint_url: str = "",
        deps: Optional[FileProcessDependencies] = None,
        settings: Optional[SettingsProvider] = None,
        bus: Optional[EventBus] = None,
    ) -> ProcessResult:
        """Process a single video file.

        Args:
            deps: Legacy callback bundle (deprecated, kept for compatibility).
            settings: New settings provider interface.
            bus: New event bus for notifications.

        Returns:
            ProcessResult with full success/failure details.
        """
        # Resolve settings: prefer new interface, fall back to deps adapter
        if settings is None and deps is not None:
            settings = _LegacySettingsAdapter(deps)
        if settings is None:
            raise ValueError("Either 'settings' or 'deps' must be provided")

        # Resolve event bus: prefer new bus, fall back to deps adapter
        if bus is None and deps is not None:
            bus = _LegacyEventBusAdapter(deps, count_claw, count)
        if bus is None:
            bus = EventBus()

        # Use new-style processing
        return self._process_new(
            filepath=filepath,
            number=number,
            mode=mode,
            count_claw=count_claw,
            count=count,
            config=config,
            movie_path=movie_path,
            failed_folder=failed_folder,
            success_folder=success_folder,
            appoint_url=appoint_url,
            settings=settings,
            bus=bus,
            deps=deps,  # pass through for legacy UI callbacks
        )

    def _process_new(
        self,
        *,
        filepath: str,
        number: str,
        mode: int,
        count_claw: int,
        count: int,
        config: Any,
        movie_path: str,
        failed_folder: str,
        success_folder: str,
        appoint_url: str,
        settings: SettingsProvider,
        bus: EventBus,
        deps: Optional[FileProcessDependencies],
    ) -> ProcessResult:
        """Core processing logic using new interfaces."""
        from core.scrape_pipeline import getDataFromJSON

        leak = 0
        uncensored = 0
        cn_sub = 0
        c_word = ""
        part = ""
        program_mode = 1 if settings.is_program_mode_move() else 2

        bus.emit(EventType.PROCESSING_START, filepath=filepath, number=number)
        bus.emit(EventType.LOG_INFO, message=f"[!]Making Data for [{filepath}], the number is [{number}]")

        # Use deps.get_json_data if available (legacy compat), otherwise use pipeline
        if deps is not None:
            json_data = deps.get_json_data(mode, number, config, appoint_url)
        else:
            json_data = getDataFromJSON(number, config, mode, appoint_url)

        if settings.is_debug_enabled():
            bus.emit(EventType.LOG_INFO, message="[+] ---Debug info---")
            for key, value in json_data.items():
                if value == "" or key == "actor_photo" or key == "extrafanart":
                    continue
                if key == "tag" and isinstance(value, list) and len(value) == 0:
                    continue
                elif key == "tag":
                    value = str(value).strip(" ['']").replace("'", "")
                bus.emit(EventType.LOG_INFO, message=f"   [+]-{key}: {value}")
            bus.emit(EventType.LOG_INFO, message="[+] ---Debug info---")

        if json_data.get("website") == "timeout":
            bus.emit(EventType.LOG_ERROR, message="[-]Connect Failed! Please check your Proxy or Network!")
            return ProcessResult(
                status=ProcessStatus.FAILED_TIMEOUT,
                filepath=filepath,
                number=number,
                error="timeout",
            )
        if not json_data.get("title"):
            bus.emit(EventType.LOG_INFO, message="[-]Movie Data not found!")
            bus.emit(EventType.SCRAPE_FAILED, filepath=filepath, failed_dir=failed_folder)
            return ProcessResult.failed_result(filepath, number, "Movie Data not found", failed_folder)
        if "http" not in json_data.get("cover", ""):
            return ProcessResult.failed_result(filepath, number, "Cover Url is None!")
        if json_data.get("imagecut") == 3 and "http" not in json_data.get("cover_small", ""):
            return ProcessResult.failed_result(filepath, number, "Cover_small Url is None!")

        if "-CD" in filepath or "-cd" in filepath:
            part = self._get_part(filepath, failed_folder, deps)
        if (
            "-c." in filepath
            or "-C." in filepath
            or "中文" in filepath
            or "字幕" in filepath
        ):
            cn_sub = 1
            c_word = "-C"
        if json_data.get("imagecut") == 3:
            uncensored = 1
        if "流出" in filepath.split("/")[-1]:
            leak = 1

        path = self._create_folder(success_folder, json_data, config, deps)
        bus.emit(EventType.LOG_INFO, message=f"[+]Folder : {path}")
        bus.emit(EventType.LOG_INFO, message=f"[+]From   : {json_data.get('website', '')}")

        number = json_data.get("number", number)
        naming_rule = str(self._get_naming_rule(json_data, deps)).replace("--", "-").strip("-")
        if leak == 1:
            naming_rule += "-流出"
        if part:
            naming_rule += part
        if cn_sub == 1:
            naming_rule += c_word

        thumb_path = path + "/" + naming_rule + "-thumb.jpg"
        poster_path = path + "/" + naming_rule + "-poster.jpg"

        if json_data.get("imagecut") == 3 and settings.should_restore_imagecut():
            json_data["imagecut"] = 0

        if program_mode == 1:
            self._thumb_download(json_data, path, naming_rule, config, filepath, failed_folder, deps)
            if settings.should_download_thumb():
                if (
                    self._small_cover_download(
                        path, naming_rule, json_data, config, filepath, failed_folder, deps
                    )
                    == "small_cover_error"
                ):
                    json_data["imagecut"] = 0
                self._cut_image(json_data["imagecut"], path, naming_rule, deps)
                self._fix_size(path, naming_rule, deps)
            if settings.should_copy_fanart():
                self._copy_fanart(path, naming_rule, deps)
            self._delete_thumb(path, naming_rule, deps)
            if self._paste_file(filepath, path, naming_rule, failed_folder, deps):
                cn_sub = 1
            if settings.should_download_nfo():
                self._print_files(path, naming_rule, cn_sub, leak, json_data, filepath, failed_folder, deps)
            if settings.is_extrafanart_enabled():
                self._extrafanart_download(json_data, path, config, filepath, failed_folder, deps)
            self._add_mark(poster_path, thumb_path, cn_sub, leak, uncensored, config, deps)
        elif program_mode == 2:
            self._paste_file(filepath, path, naming_rule, failed_folder, deps)

        json_data["thumb_path"] = thumb_path
        json_data["poster_path"] = poster_path
        json_data["number"] = number

        self._add_label_info(json_data, deps)

        suffix = part + c_word
        bus.emit(EventType.SCRAPE_SUCCESS,
                 count_claw=count_claw, count=count,
                 number=number, suffix=suffix,
                 json_data=json_data)

        return ProcessResult.success_result(
            filepath, number, json_data, path, suffix
        )

    # --- Legacy callback wrappers ---

    def _get_part(self, filepath, failed_folder, deps):
        if deps:
            return deps.get_part(filepath, failed_folder)
        return ""

    def _create_folder(self, success_folder, json_data, config, deps):
        if deps:
            return deps.create_folder(success_folder, json_data, config)
        import os
        path = success_folder + "/" + json_data.get("title", "unknown")
        os.makedirs(path, exist_ok=True)
        return path

    def _get_naming_rule(self, json_data, deps):
        if deps:
            return deps.get_naming_rule(json_data)
        return json_data.get("number", "")

    def _thumb_download(self, json_data, path, naming_rule, config, filepath, failed_folder, deps):
        if deps:
            deps.thumb_download(json_data, path, naming_rule, config, filepath, failed_folder)

    def _small_cover_download(self, path, naming_rule, json_data, config, filepath, failed_folder, deps):
        if deps:
            return deps.small_cover_download(path, naming_rule, json_data, config, filepath, failed_folder)
        return ""

    def _cut_image(self, imagecut, path, naming_rule, deps):
        if deps:
            deps.cut_image(imagecut, path, naming_rule)

    def _fix_size(self, path, naming_rule, deps):
        if deps:
            deps.fix_size(path, naming_rule)

    def _copy_fanart(self, path, naming_rule, deps):
        if deps:
            deps.copy_fanart(path, naming_rule)

    def _delete_thumb(self, path, naming_rule, deps):
        if deps:
            deps.delete_thumb(path, naming_rule)

    def _paste_file(self, filepath, path, naming_rule, failed_folder, deps):
        if deps:
            return deps.paste_file(filepath, path, naming_rule, failed_folder)
        return True

    def _print_files(self, path, naming_rule, cn_sub, leak, json_data, filepath, failed_folder, deps):
        if deps:
            deps.print_files(path, naming_rule, cn_sub, leak, json_data, filepath, failed_folder)

    def _extrafanart_download(self, json_data, path, config, filepath, failed_folder, deps):
        if deps:
            deps.extrafanart_download(json_data, path, config, filepath, failed_folder)

    def _add_mark(self, poster_path, thumb_path, cn_sub, leak, uncensored, config, deps):
        if deps:
            deps.add_mark(poster_path, thumb_path, cn_sub, leak, uncensored, config)

    def _add_label_info(self, json_data, deps):
        if deps:
            deps.add_label_info(json_data)
