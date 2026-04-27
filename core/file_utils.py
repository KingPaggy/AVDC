#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
from configparser import ConfigParser
from PIL import Image


RE_CD = re.compile(r"-CD\d+", re.IGNORECASE)
RE_DATE = re.compile(r"-\d{4}-\d{1,2}-\d{1,2}|\d{4}-\d{1,2}-\d{1,2}-")
RE_EUROPEAN = re.compile(r"^\D+\.\d{2}\.\d{2}\.\d{2}")
RE_EUROPEAN_NUM = re.compile(r"\D+\.\d{2}\.\d{2}\.\d{2}")
RE_XXX_AV = re.compile(r"XXX-AV-\d{4,}", re.IGNORECASE)
RE_FC2 = re.compile(r"FC2-\d{5,}", re.IGNORECASE)
RE_ALPHA_DASH_NUM = re.compile(r"[a-zA-Z]+-\d+")
RE_WORD_DASH_NUM = re.compile(r"\w+-\d+")
RE_NUM_ALPHA_DASH = re.compile(r"\d+[a-zA-Z]+-\d+")
RE_ALPHA_DASH_ALPHA_NUM = re.compile(r"[a-zA-Z]+-[a-zA-Z]\d+")
RE_NUM_DASH_ALPHA = re.compile(r"\d+-[a-zA-Z]+")
RE_NUM_DASH = re.compile(r"\d+-\d+")
RE_NUM_UNDER = re.compile(r"\d+_\d+")
RE_DMM_STYLE = re.compile(r"\D{2,}00\d{3,}")
RE_ALL_NUM = re.compile(r"\d+")
RE_ALL_ALPHA = re.compile(r"\D+")
RE_ESCAPE_SPLIT = re.compile(r"[,，]")
RE_HIDDEN_FILE = re.compile(r"^\..+")


def escapePath(path, Config):
    escapeLiterals = Config["escape"]["literals"]
    backslash = "\\"
    for literal in escapeLiterals:
        path = path.replace(backslash + literal, "")
    return path


def movie_lists(escape_folder, movie_type, movie_path):
    if escape_folder != "":
        escape_folder = RE_ESCAPE_SPLIT.split(escape_folder)
    total = []
    file_type = movie_type.split("|")
    file_root = movie_path.replace("\\", "/")
    for root, dirs, files in os.walk(file_root):
        if escape_folder != "":
            flag_escape = 0
            for folder in escape_folder:
                if folder in root:
                    flag_escape = 1
                    break
            if flag_escape == 1:
                continue
        for f in files:
            file_type_current = os.path.splitext(f)[1]
            file_name = os.path.splitext(f)[0]
            if RE_HIDDEN_FILE.search(file_name):
                continue
            if file_type_current in file_type:
                path = root + "/" + f
                path = path.replace("\\\\", "/").replace("\\", "/")
                total.append(path)
    return total


def getNumber(filepath, escape_string):
    filepath = filepath.replace("-C.", ".").replace("-c.", ".")
    filename = os.path.splitext(filepath.split("/")[-1])[0]
    escape_string_list = RE_ESCAPE_SPLIT.split(escape_string)
    for string in escape_string_list:
        if string in filename:
            filename = filename.replace(string, "")
    part = RE_CD.findall(filename)
    if part:
        part = part[0]
    else:
        part = ""
    filename = filename.replace(part, "")
    filename = RE_DATE.sub("", filename)
    if RE_EUROPEAN.search(filename):
        match = RE_EUROPEAN_NUM.search(filename)
        if match:
            return match.group()
        return os.path.splitext(filepath.split("/")[-1])[0]
    elif RE_XXX_AV.search(filename.upper()):
        return RE_XXX_AV.search(filename.upper()).group()
    elif "-" in filename or "_" in filename:
        if "FC2" or "fc2" in filename:
            filename = filename.upper().replace("PPV", "").replace("--", "-")
        fc2_match = RE_FC2.search(filename)
        if fc2_match:
            return fc2_match.group()
        match = RE_NUM_ALPHA_DASH.search(filename)
        if match:
            return match.group()
        match = RE_ALPHA_DASH_NUM.search(filename)
        if match:
            return match.group()
        match = RE_ALPHA_DASH_ALPHA_NUM.search(filename)
        if match:
            return match.group()
        match = RE_NUM_DASH_ALPHA.search(filename)
        if match:
            return match.group()
        match = RE_NUM_DASH.search(filename)
        if match:
            return match.group()
        match = RE_NUM_UNDER.search(filename)
        if match:
            return match.group()
        return filename
    else:
        try:
            file_number = os.path.splitext(filename.split("/")[-1])[0]
            find_num = RE_ALL_NUM.findall(file_number)
            find_char = RE_ALL_ALPHA.findall(file_number)
            if find_num and find_char:
                if len(find_num[0]) <= 4 and len(find_char[0]) > 1:
                    file_number = find_char[0] + "-" + find_num[0]
            return file_number
        except Exception:
            return os.path.splitext(filepath.split("/")[-1])[0]


def is_uncensored(number):
    if (
        re.match(r"^\d{4,}", number)
        or re.match(r"n\d{4}", number)
        or "HEYZO" in number.upper()
    ):
        return True
    config = get_config()
    prefix_list = str(config["uncensored"]["uncensored_prefix"]).split("|")
    for pre in prefix_list:
        if pre.upper() in number.upper():
            return True
    return False


def getDataState(json_data):
    if (
        json_data["title"] == ""
        or json_data["title"] == "None"
        or json_data["title"] == "null"
    ):
        return 0
    else:
        return 1


def get_config():
    config_file = ""
    if os.path.exists("../config.ini"):
        config_file = "../config.ini"
    elif os.path.exists("config.ini"):
        config_file = "config.ini"
    config = ConfigParser()
    config.read(config_file, encoding="UTF-8")
    return config


def check_pic(path_pic):
    try:
        img = Image.open(path_pic)
        img.load()
        return True
    except (FileNotFoundError, OSError):
        return False

