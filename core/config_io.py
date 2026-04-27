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
    return config


def get_proxy_config():
    """Return (proxy_type, proxy, timeout, retry_count) from the proxy section."""
    config = get_config()
    proxy_type = str(config["proxy"]["type"])
    proxy = str(config["proxy"]["proxy"])
    timeout = int(config["proxy"]["timeout"])
    retry_count = int(config["proxy"]["retry"])
    return proxy_type, proxy, timeout, retry_count


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
