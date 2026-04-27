#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from core.file_utils import getDataState, is_uncensored
from core.errors import ScrapingError
from core.scraper_adapter import clear_cache, cache_key, get_cached, set_cache
from core.scraper_dispatcher import ScraperDispatcher

_SCRAPER_MODULES = None


def get_scraper_modules():
    global _SCRAPER_MODULES
    if _SCRAPER_MODULES is None:
        from Getter import avsox, javbus, javdb, mgstage, dmm, jav321, xcity

        _SCRAPER_MODULES = {
            "avsox": avsox,
            "javbus": javbus,
            "javdb": javdb,
            "mgstage": mgstage,
            "dmm": dmm,
            "jav321": jav321,
            "xcity": xcity,
        }
    return _SCRAPER_MODULES


def _call_scraper(method_path, scrapers, number, appoint_url, isuncensored=False):
    """Call a scraper method by its dotted path string. Returns raw JSON string."""
    module_name, method_name = method_path.rsplit(".", 1)
    module = scrapers[module_name]
    method = getattr(module, method_name)
    if method_name == "main" and module_name == "jav321" and isuncensored:
        return method(number, isuncensored, appoint_url)
    if method_name == "main" and module_name == "javdb":
        return method(number, appoint_url, isuncensored)
    return method(number, appoint_url)


def _execute_chain(scrapers, chain, number, appoint_url, isuncensored=False):
    """Execute scraper chain, returning (json_data, working_number).

    Returns the last attempted result even if unsuccessful, to preserve
    the short-circuit behavior for empty-title and timeout cases.
    """
    working_number = number
    last_result = {}
    for i, (method_path, _priority) in enumerate(chain):
        # Check cache first
        key = cache_key(method_path, working_number)
        cached = get_cached(key, "")
        if cached is not None:
            try:
                json_data = json.loads(cached)
                last_result = json_data
                if getDataState(json_data) == 1:
                    return json_data, working_number
            except json.JSONDecodeError:
                pass
            continue

        try:
            result = _call_scraper(method_path, scrapers, working_number, appoint_url, isuncensored)
            if not isinstance(result, str):
                continue
            json_data = json.loads(result)
            # Only cache successful results
            if getDataState(json_data) == 1:
                set_cache(key, result)
            last_result = json_data
            if getDataState(json_data) == 1:
                return json_data, working_number
            # mgstage normalizes number after first call for subsequent scrapers
            if method_path.startswith("mgstage.") and i == 0:
                m = re.search(r"[a-zA-Z]+-\d+", working_number)
                if m:
                    working_number = m.group()
        except (json.JSONDecodeError, ScrapingError):
            pass
        except Exception as e:
            print(f"[!]Scraper {method_path} error: {e}")
            pass
    return last_result, working_number


def getDataFromJSON(file_number, config, mode, appoint_url):
    scrapers = get_scraper_modules()
    isuncensored = is_uncensored(file_number)
    json_data = {}

    # Delegate chain selection to ScraperDispatcher
    chain = ScraperDispatcher.get_scraper_chain(file_number, mode)

    if not chain and ScraperDispatcher.is_dmm_style(file_number) and mode not in (1, 7):
        json_data = {"title": "", "actor": "", "website": ""}
    elif not chain:
        json_data = {"title": "", "actor": "", "website": ""}
    else:
        json_data, _ = _execute_chain(scrapers, chain, file_number, appoint_url, isuncensored)

    if json_data.get("website") == "timeout":
        return json_data
    if not json_data or json_data.get("title") == "":
        return json_data

    title = json_data["title"]
    number = json_data["number"]
    actor_list = str(json_data["actor"]).strip("[ ]").replace("'", "").split(",")
    release = json_data["release"]
    cover_small = json_data.get("cover_small", "")
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
