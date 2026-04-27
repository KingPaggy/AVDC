#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backward-compatible wrappers for the new core modules.

The UI and tests are being migrated to import from :mod:`core.*` directly, but
this module remains as a compatibility layer so older call sites keep working
while the refactor lands in small steps.
"""

from core.config_io import get_config, save_config
from core.file_utils import (
    check_pic,
    escapePath,
    getDataState,
    getNumber,
    is_uncensored,
    movie_lists,
)
from core.metadata import get_info
from core.scrape_pipeline import getDataFromJSON

__all__ = [
    "get_config",
    "save_config",
    "movie_lists",
    "escapePath",
    "getNumber",
    "check_pic",
    "get_info",
    "getDataFromJSON",
    "getDataState",
    "is_uncensored",
]

