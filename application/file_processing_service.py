#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable, Dict, Any


@dataclass
class FileProcessDependencies:
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
        deps: FileProcessDependencies,
    ) -> str:
        leak = 0
        uncensored = 0
        cn_sub = 0
        c_word = ""
        multi_part = 0
        part = ""
        program_mode = 1 if deps.is_program_mode_move() else 2

        json_data = deps.get_json_data(mode, number, config, appoint_url)

        if deps.is_debug_enabled():
            deps.debug(json_data)

        if json_data["website"] == "timeout":
            deps.log("[-]Connect Failed! Please check your Proxy or Network!")
            return "error"
        if json_data["title"] == "":
            deps.log("[-]Movie Data not found!")
            deps.move_failed_folder(filepath, failed_folder)
            return "not found"
        if "http" not in json_data["cover"]:
            raise Exception("Cover Url is None!")
        if json_data["imagecut"] == 3 and "http" not in json_data["cover_small"]:
            raise Exception("Cover_small Url is None!")

        if "-CD" in filepath or "-cd" in filepath:
            multi_part = 1
            part = deps.get_part(filepath, failed_folder)
        if (
            "-c." in filepath
            or "-C." in filepath
            or "中文" in filepath
            or "字幕" in filepath
        ):
            cn_sub = 1
            c_word = "-C"
        if json_data["imagecut"] == 3:
            uncensored = 1
        if "流出" in filepath.split("/")[-1]:
            leak = 1

        path = deps.create_folder(success_folder, json_data, config)
        deps.log("[+]Folder : " + path)
        deps.log("[+]From   : " + json_data["website"])

        number = json_data["number"]
        naming_rule = str(deps.get_naming_rule(json_data)).replace("--", "-").strip("-")
        if leak == 1:
            naming_rule += "-流出"
        if multi_part == 1:
            naming_rule += part
        if cn_sub == 1:
            naming_rule += c_word

        thumb_path = path + "/" + naming_rule + "-thumb.jpg"
        poster_path = path + "/" + naming_rule + "-poster.jpg"

        if json_data["imagecut"] == 3 and deps.is_restore_imagecut_enabled():
            json_data["imagecut"] = 0

        if program_mode == 1:
            deps.thumb_download(json_data, path, naming_rule, config, filepath, failed_folder)
            if deps.is_show_small_cover():
                if (
                    deps.small_cover_download(
                        path, naming_rule, json_data, config, filepath, failed_folder
                    )
                    == "small_cover_error"
                ):
                    json_data["imagecut"] = 0
                deps.cut_image(json_data["imagecut"], path, naming_rule)
                deps.fix_size(path, naming_rule)
            if deps.is_copy_fanart_enabled():
                deps.copy_fanart(path, naming_rule)
            deps.delete_thumb(path, naming_rule)
            if deps.paste_file(filepath, path, naming_rule, failed_folder):
                cn_sub = 1
            if deps.is_print_enabled():
                deps.print_files(path, naming_rule, cn_sub, leak, json_data, filepath, failed_folder)
            if deps.is_extrafanart_enabled():
                deps.extrafanart_download(json_data, path, config, filepath, failed_folder)
            deps.add_mark(poster_path, thumb_path, cn_sub, leak, uncensored, config)
        elif program_mode == 2:
            deps.paste_file(filepath, path, naming_rule, failed_folder)

        json_data["thumb_path"] = thumb_path
        json_data["poster_path"] = poster_path
        json_data["number"] = number
        deps.add_label_info(json_data)
        deps.register_result(count_claw, count, json_data)
        return part + c_word
