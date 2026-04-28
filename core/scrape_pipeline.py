#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import concurrent.futures
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


def _try_single_scraper(method_path, scrapers, working_number, appoint_url, isuncensored):
    """Try one scraper. Returns (json_data, working_number) or (None, working_number)."""
    key = cache_key(method_path, working_number)
    cached = get_cached(key, "")
    if cached is not None:
        try:
            json_data = json.loads(cached)
            return json_data, working_number
        except json.JSONDecodeError:
            pass

    try:
        result = _call_scraper(method_path, scrapers, working_number, appoint_url, isuncensored)
        if not isinstance(result, str):
            return None, working_number
        json_data = json.loads(result)
        if getDataState(json_data) == 1:
            set_cache(key, result)
        return json_data, working_number
    except (json.JSONDecodeError, ScrapingError):
        pass
    except Exception:
        pass
    return None, working_number


def _execute_chain(scrapers, chain, number, appoint_url, isuncensored=False, max_concurrent=1):
    """Execute scraper chain, returning first successful result.

    When max_concurrent == 1 (default): sequential execution.
    When max_concurrent > 1: launch up to max_concurrent scrapers in parallel,
    return the first successful result. Remaining scrapers are cancelled.

    Results are cached to avoid repeated network requests for the same
    (scraper, number) pair within the TTL window.
    """
    if max_concurrent <= 1:
        return _execute_sequential(scrapers, chain, number, appoint_url, isuncensored)
    return _execute_concurrent(scrapers, chain, number, appoint_url, isuncensored, max_concurrent)


def _execute_sequential(scrapers, chain, number, appoint_url, isuncensored):
    """Execute scraper chain sequentially, returning first successful result."""
    working_number = number
    last_result = {}

    for i, (method_path, _priority) in enumerate(chain):
        json_data, wn = _try_single_scraper(method_path, scrapers, working_number, appoint_url, isuncensored)
        if json_data and getDataState(json_data) == 1:
            return _to_movie(json_data), wn
        if json_data:
            last_result = json_data
            # mgstage normalizes number after first call
            if method_path.startswith("mgstage.") and i == 0:
                m = re.search(r"[a-zA-Z]+-\d+", working_number)
                if m:
                    working_number = m.group()

    return _to_movie(last_result), working_number


def _execute_concurrent(scrapers, chain, number, appoint_url, isuncensored, max_workers):
    """Execute scraper chain concurrently, returning first successful result."""
    working_number = number
    last_result = {}
    batch_start = 0

    while batch_start < len(chain):
        batch_end = min(batch_start + max_workers, len(chain))
        batch = list(enumerate(chain[batch_start:batch_end], start=batch_start))

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
            future_to_idx = {}
            for i, (method_path, _priority) in batch:
                fut = executor.submit(
                    _try_single_scraper,
                    method_path, scrapers, working_number, appoint_url, isuncensored,
                )
                future_to_idx[fut] = i

            # Collect results in completion order
            batch_results = {}
            for fut in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[fut]
                try:
                    json_data, wn = fut.result()
                    batch_results[idx] = (json_data, wn)
                except Exception:
                    batch_results[idx] = (None, working_number)

        # Check results in chain order (lower index = higher priority)
        for i in range(batch_start, batch_end):
            json_data, wn = batch_results.get(i, (None, working_number))
            if json_data and getDataState(json_data) == 1:
                return _to_movie(json_data), wn
            if json_data:
                last_result = json_data
                # mgstage normalizes number after first call
                if chain[i][0].startswith("mgstage.") and i == 0:
                    m = re.search(r"[a-zA-Z]+-\d+", working_number)
                    if m:
                        working_number = m.group()

        batch_start = batch_end

    return _to_movie(last_result), working_number


def getDataFromJSON(file_number, config, mode, appoint_url):
    scrapers = get_scraper_modules()
    isuncensored = is_uncensored(file_number)

    # Read concurrent scraper limit from config (default: 1 = sequential)
    try:
        max_concurrent = int(config.get("common", "max_concurrent", fallback="1"))
    except (ValueError, TypeError):
        max_concurrent = 1
    max_concurrent = max(1, min(max_concurrent, 5))  # clamp 1-5

    # Delegate chain selection to ScraperDispatcher
    chain = ScraperDispatcher.get_scraper_chain(file_number, mode)

    if not chain and ScraperDispatcher.is_dmm_style(file_number) and mode not in (1, 7):
        return {"title": "", "actor": "", "website": ""}
    elif not chain:
        return {"title": "", "actor": "", "website": ""}
    else:
        movie, _ = _execute_chain(scrapers, chain, file_number, appoint_url, isuncensored, max_concurrent)

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
