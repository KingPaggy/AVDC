#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os


def get_config_file() -> str:
    if os.path.exists("../config.ini"):
        return "../config.ini"
    if os.path.exists("config.ini"):
        return "config.ini"
    return "config.ini"


def get_config():
    from configparser import ConfigParser

    config = ConfigParser()
    config.read(get_config_file(), encoding="UTF-8")
    # Ensure all expected sections exist with defaults
    _apply_defaults(config)
    return config


_DEFAULTS = {
    "common": {
        "main_mode": "1",
        "failed_output_folder": "failed",
        "success_output_folder": "JAV_output",
        "failed_file_move": "1",
        "soft_link": "0",
        "show_poster": "1",
        "website": "all",
    },
    "proxy": {
        "type": "no",
        "proxy": "",
        "timeout": "7",
        "retry": "3",
    },
    "Name_Rule": {
        "folder_name": "actor/number-title-release",
        "naming_media": "number-title",
        "naming_file": "number",
    },
    "update": {
        "update_check": "1",
    },
    "log": {
        "save_log": "1",
    },
    "media": {
        "media_type": ".mp4|.avi|.rmvb|.wmv|.mov|.mkv",
        "sub_type": ".srt|.ass|.ssa",
        "media_path": ".",
    },
    "escape": {
        "literals": r"\()",
        "folders": "failed,JAV_output",
        "string": "",
    },
    "debug_mode": {
        "switch": "0",
    },
    "emby": {
        "emby_url": "localhost:8096",
        "api_key": "",
    },
    "mark": {
        "poster_mark": "1",
        "thumb_mark": "1",
        "mark_size": "3",
        "mark_type": "SUB,LEAK,UNCENSORED",
        "mark_pos": "top_left",
    },
    "uncensored": {
        "uncensored_prefix": "S2M|BT|LAF|SMD",
        "uncensored_poster": "0",
    },
    "file_download": {
        "nfo": "1",
        "poster": "1",
        "fanart": "1",
        "thumb": "1",
    },
    "extrafanart": {
        "extrafanart_download": "0",
        "extrafanart_folder": "extrafanart",
    },
}


def _apply_defaults(config):
    """Fill missing sections/keys with defaults without overwriting existing values."""
    for section, defaults in _DEFAULTS.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in defaults.items():
            if not config.has_option(section, key):
                config.set(section, key, value)


def get_config():
    from configparser import ConfigParser

    config = ConfigParser()
    config.read(get_config_file(), encoding="UTF-8")
    _apply_defaults(config)
    return config


def get_proxy_config():
    """Return (proxy_type, proxy, timeout, retry_count) from the proxy section."""
    config = get_config()
    proxy_type = str(config["proxy"]["type"])
    proxy = str(config["proxy"]["proxy"])
    timeout = int(config["proxy"]["timeout"])
    retry_count = int(config["proxy"]["retry"])
    return proxy_type, proxy, timeout, retry_count


def get_default_config() -> dict:
    """Return the default configuration dictionary."""
    return {
        "show_poster": 1,
        "main_mode": 1,
        "soft_link": 0,
        "switch_debug": 1,
        "failed_file_move": 1,
        "update_check": 1,
        "save_log": 1,
        "website": "all",
        "failed_output_folder": "failed",
        "success_output_folder": "JAV_output",
        "proxy": "",
        "timeout": 7,
        "retry": 3,
        "folder_name": "actor/number-title-release",
        "naming_media": "number-title",
        "naming_file": "number",
        "literals": r"\()",
        "folders": "failed,JAV_output",
        "string": "1080p,720p,22-sht.me,-HD",
        "emby_url": "localhost:8096",
        "api_key": "",
        "media_path": "E:/TEMP",
        "media_type": ".mp4|.avi|.rmvb|.wmv|.mov|.mkv|.flv|.ts|.webm|.MP4|.AVI|.RMVB|.WMV|.MOV|.MKV|.FLV|.TS|.WEBM",
        "sub_type": ".smi|.srt|.idx|.sub|.sup|.psb|.ssa|.ass|.txt|.usf|.xss|.ssf|.rt|.lrc|.sbv|.vtt|.ttml",
        "poster_mark": 1,
        "thumb_mark": 1,
        "mark_size": 3,
        "mark_type": "SUB,LEAK,UNCENSORED",
        "mark_pos": "top_left",
        "uncensored_poster": 0,
        "uncensored_prefix": "S2M|BT|LAF|SMD",
        "nfo_download": 1,
        "poster_download": 1,
        "fanart_download": 1,
        "thumb_download": 1,
        "extrafanart_download": 0,
        "extrafanart_folder": "extrafanart",
    }


def save_config(json_config):
    config_file = get_config_file()
    with open(config_file, "wt", encoding="UTF-8") as code:
        print("[common]", file=code)
        print("main_mode = " + str(json_config["main_mode"]), file=code)
        print(
            "failed_output_folder = " + json_config["failed_output_folder"], file=code
        )
        print(
            "success_output_folder = " + json_config["success_output_folder"], file=code
        )
        print("failed_file_move = " + str(json_config["failed_file_move"]), file=code)
        print("soft_link = " + str(json_config["soft_link"]), file=code)
        print("show_poster = " + str(json_config["show_poster"]), file=code)
        print("website = " + json_config["website"], file=code)
        print(
            "# all or mgstage or fc2club or javbus or jav321 or javdb or avsox or xcity or dmm",
            file=code,
        )
        print("", file=code)
        print("[proxy]", file=code)
        print("type = " + json_config["type"], file=code)
        print("proxy = " + json_config["proxy"], file=code)
        print("timeout = " + str(json_config["timeout"]), file=code)
        print("retry = " + str(json_config["retry"]), file=code)
        print("# type: no, http, socks5", file=code)
        print("", file=code)
        print("[Name_Rule]", file=code)
        print("folder_name = " + json_config["folder_name"], file=code)
        print("naming_media = " + json_config["naming_media"], file=code)
        print("naming_file = " + json_config["naming_file"], file=code)
        print("", file=code)
        print("[update]", file=code)
        print("update_check = " + str(json_config["update_check"]), file=code)
        print("", file=code)
        print("[log]", file=code)
        print("save_log = " + str(json_config["save_log"]), file=code)
        print("", file=code)
        print("[media]", file=code)
        print("media_type = " + json_config["media_type"], file=code)
        print("sub_type = " + json_config["sub_type"], file=code)
        print("media_path = " + json_config["media_path"], file=code)
        print("", file=code)
        print("[escape]", file=code)
        print("literals = " + json_config["literals"], file=code)
        print("folders = " + json_config["folders"], file=code)
        print("string = " + json_config["string"], file=code)
        print("", file=code)
        print("[debug_mode]", file=code)
        print("switch = " + str(json_config["switch_debug"]), file=code)
        print("", file=code)
        print("[emby]", file=code)
        print("emby_url = " + json_config["emby_url"], file=code)
        print("api_key = " + json_config["api_key"], file=code)
        print("", file=code)
        print("[mark]", file=code)
        print("poster_mark = " + str(json_config["poster_mark"]), file=code)
        print("thumb_mark = " + str(json_config["thumb_mark"]), file=code)
        print("mark_size = " + str(json_config["mark_size"]), file=code)
        print("mark_type = " + json_config["mark_type"], file=code)
        print("mark_pos = " + json_config["mark_pos"], file=code)
        print("# mark_size : range 1-5", file=code)
        print("# mark_type : sub, leak, uncensored", file=code)
        print(
            "# mark_pos  : bottom_right or bottom_left or top_right or top_left",
            file=code,
        )
        print("", file=code)
        print("[uncensored]", file=code)
        print("uncensored_prefix = " + str(json_config["uncensored_prefix"]), file=code)
        print("uncensored_poster = " + str(json_config["uncensored_poster"]), file=code)
        print("# 0 : official, 1 : cut", file=code)
        print("", file=code)
        print("[file_download]", file=code)
        print("nfo = " + str(json_config["nfo_download"]), file=code)
        print("poster = " + str(json_config["poster_download"]), file=code)
        print("fanart = " + str(json_config["fanart_download"]), file=code)
        print("thumb = " + str(json_config["thumb_download"]), file=code)
        print("", file=code)
        print("[extrafanart]", file=code)
        print(
            "extrafanart_download = " + str(json_config["extrafanart_download"]),
            file=code,
        )
        print(
            "extrafanart_folder = " + str(json_config["extrafanart_folder"]), file=code
        )
