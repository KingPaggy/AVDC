#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re

from Getter import avsox, javbus, javdb, mgstage, dmm, jav321, xcity
from core.file_utils import getDataState, is_uncensored


def getDataFromJSON(file_number, config, mode, appoint_url):
    isuncensored = is_uncensored(file_number)
    json_data = {}
    if mode == 1:
        if isuncensored:
            json_data = json.loads(javbus.main_uncensored(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(javdb.main(file_number, appoint_url, True))
            if getDataState(json_data) == 0 and "HEYZO" in file_number.upper():
                json_data = json.loads(jav321.main(file_number, appoint_url, True))
            if getDataState(json_data) == 0:
                json_data = json.loads(avsox.main(file_number, appoint_url))
        elif re.match(r"\d+[a-zA-Z]+-\d+", file_number) or "SIRO" in file_number.upper():
            json_data = json.loads(mgstage.main(file_number, appoint_url))
            file_number = re.search(r"[a-zA-Z]+-\d+", file_number).group()
            if getDataState(json_data) == 0:
                json_data = json.loads(jav321.main(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(javdb.main(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(javbus.main(file_number, appoint_url))
        elif "FC2" in file_number.upper():
            json_data = json.loads(javdb.main(file_number, appoint_url))
        elif re.match(r"\D{2,}00\d{3,}", file_number) and "-" not in file_number and "_" not in file_number:
            json_data = json.loads(dmm.main(file_number, appoint_url))
        elif re.search(r"\D+\.\d{2}\.\d{2}\.\d{2}", file_number):
            json_data = json.loads(javdb.main_us(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(javbus.main_us(file_number, appoint_url))
        else:
            json_data = json.loads(javbus.main(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(jav321.main(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(xcity.main(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(javdb.main(file_number, appoint_url))
            if getDataState(json_data) == 0:
                json_data = json.loads(avsox.main(file_number, appoint_url))
    elif re.match(r"\D{2,}00\d{3,}", file_number) and mode != 7:
        json_data = {
            "title": "",
            "actor": "",
            "website": "",
        }
    elif mode == 2:
        json_data = json.loads(mgstage.main(file_number, appoint_url))
    elif mode == 3:
        if isuncensored:
            json_data = json.loads(javbus.main_uncensored(file_number, appoint_url))
        elif re.search(r"\D+\.\d{2}\.\d{2}\.\d{2}", file_number):
            json_data = json.loads(javbus.main_us(file_number, appoint_url))
        else:
            json_data = json.loads(javbus.main(file_number, appoint_url))
    elif mode == 4:
        json_data = json.loads(jav321.main(file_number, isuncensored, appoint_url))
    elif mode == 5:
        if re.search(r"\D+\.\d{2}\.\d{2}\.\d{2}", file_number):
            json_data = json.loads(javdb.main_us(file_number, appoint_url))
        else:
            json_data = json.loads(javdb.main(file_number, appoint_url, isuncensored))
    elif mode == 6:
        json_data = json.loads(avsox.main(file_number, appoint_url))
    elif mode == 7:
        json_data = json.loads(xcity.main(file_number, appoint_url))
    elif mode == 8:
        json_data = json.loads(dmm.main(file_number, appoint_url))

    if json_data["website"] == "timeout":
        return json_data
    elif json_data["title"] == "":
        return json_data

    title = json_data["title"]
    number = json_data["number"]
    actor_list = str(json_data["actor"]).strip("[ ]").replace("'", "").split(",")
    release = json_data["release"]
    try:
        cover_small = json_data["cover_small"]
    except Exception:
        cover_small = ""
    tag = str(json_data["tag"]).strip("[ ]").replace("'", "").replace(" ", "").split(",")
    actor = str(actor_list).strip("[ ]").replace("'", "").replace(" ", "")
    if actor == "":
        actor = "Unknown"

    title = title.replace("\\", "")
    title = title.replace("/", "")
    title = title.replace(":", "")
    title = title.replace("*", "")
    title = title.replace("?", "")
    title = title.replace('"', "")
    title = title.replace("<", "")
    title = title.replace(">", "")
    title = title.replace("|", "")
    title = title.replace(" ", ".")
    title = title.replace("【", "")
    title = title.replace("】", "")
    release = release.replace("/", "-")
    tmpArr = cover_small.split(",")
    if len(tmpArr) > 0:
        cover_small = tmpArr[0].strip('"').strip("'")
    for key, value in json_data.items():
        if key in ("title", "studio", "director", "series", "publisher"):
            json_data[key] = str(value).replace("/", "")

    naming_media = config["Name_Rule"]["naming_media"]
    naming_file = config["Name_Rule"]["naming_file"]
    folder_name = config["Name_Rule"]["folder_name"]

    json_data["title"] = title
    json_data["number"] = number
    json_data["actor"] = actor
    json_data["release"] = release
    json_data["cover_small"] = cover_small
    json_data["tag"] = tag
    json_data["naming_media"] = naming_media
    json_data["naming_file"] = naming_file
    json_data["folder_name"] = folder_name
    return json_data

