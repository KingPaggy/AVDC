#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
from core.file_utils import getDataState, is_uncensored
from core.errors import ScrapingError
from core.models import Movie
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


def _to_movie(json_data: dict) -> Movie:
    """Convert raw scraper dict to typed Movie, normalizing fields."""
    if not json_data:
        return Movie.empty()

    movie = Movie.from_dict(json_data)

    # Don't sanitize timeout results or empty results — preserve raw data
    if json_data.get("website") == "timeout" or getDataState(json_data) == 0:
        return movie

    # Sanitize title
    movie.title = movie.title.replace("\\", "").replace("/", "").replace(":", "").replace("*", "").replace("?", "").replace('"', "").replace("<", "").replace(">", "").replace("|", "").replace(" ", ".").replace("【", "").replace("】", "")
    # Sanitize release
    movie.release = movie.release.replace("/", "-")
    # Sanitize text fields
    for field in ("title", "studio", "director", "series", "publisher"):
        setattr(movie, field, getattr(movie, field, "").replace("/", ""))
    # Normalize empty actor
    if not movie.actor:
        movie.actor = ["Unknown"]
    return movie


def _execute_chain(scrapers, chain, number, appoint_url, isuncensored=False):
    """Execute scraper chain, returning (Movie, working_number).

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
                    return _to_movie(json_data), working_number
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
                return _to_movie(json_data), working_number
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
    return _to_movie(last_result), working_number


def getDataFromJSON(file_number, config, mode, appoint_url):
    scrapers = get_scraper_modules()
    isuncensored = is_uncensored(file_number)

    # Delegate chain selection to ScraperDispatcher
    chain = ScraperDispatcher.get_scraper_chain(file_number, mode)

    if not chain and ScraperDispatcher.is_dmm_style(file_number) and mode not in (1, 7):
        return {"title": "", "actor": "", "website": ""}
    elif not chain:
        return {"title": "", "actor": "", "website": ""}
    else:
        movie, _ = _execute_chain(scrapers, chain, file_number, appoint_url, isuncensored)

    if movie.website == "timeout":
        return movie.to_dict()
    if not movie.is_valid():
        d = movie.to_dict()
        # Ensure backward-compatible empty format
        d["actor"] = ""
        d["tag"] = []
        return d

    # Apply naming rules
    naming_media = config["Name_Rule"]["naming_media"]
    naming_file = config["Name_Rule"]["naming_file"]
    folder_name = config["Name_Rule"]["folder_name"]

    movie_dict = movie.to_dict()
    # Flatten actor list to string for backward compatibility
    if isinstance(movie_dict.get("actor"), list):
        movie_dict["actor"] = str(movie_dict["actor"]).strip("[ ]").replace("'", "").replace(" ", "")
        if movie_dict["actor"] == "":
            movie_dict["actor"] = "Unknown"
    # Flatten tag list
    if isinstance(movie_dict.get("tag"), list):
        movie_dict["tag"] = str(movie_dict["tag"]).strip("[ ]").replace("'", "").replace(" ", "").split(",")
    movie_dict["naming_media"] = naming_media
    movie_dict["naming_file"] = naming_file
    movie_dict["folder_name"] = folder_name
    return movie_dict
