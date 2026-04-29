#!/usr/bin/env python3
"""Quick real-number scrape test — prints full JSON results."""
import sys
import os
import json
from configparser import ConfigParser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core._config.config_io import get_config
from core._files.file_utils import getNumber, is_uncensored
from core._scraper.scrape_pipeline import getDataFromJSON

# Real numbers to test, covering each category
TEST_NUMBERS = [
    ("SSIS-487",       "standard censored"),
    ("FC2-3052557",    "FC2"),
    ("HEYZO-3032",     "uncensored"),
    ("259LUXU-504",    "mgstage style"),
    ("sexart.19.11.03", "european"),
]

FIELDS_TO_SHOW = [
    "title", "number", "actor", "studio", "publisher",
    "director", "release", "runtime", "year", "score",
    "outline", "tag", "series", "cover", "cover_small",
    "website", "source", "imagecut", "actor_photo",
    "extrafanart",
]

def main():
    config = get_config()

    print(f"{'='*60}")
    print(f"  Real-Number Scrape Test")
    print(f"  Config: website={config.get('common','website', fallback='?')}, mode=1 (all)")
    print(f"{'='*60}")

    for number, label in TEST_NUMBERS:
        print(f"\n{'─'*60}")
        print(f"  [{number}]  ({label})")
        print(f"  is_uncensored: {is_uncensored(number)}")
        print(f"{'─'*60}")

        try:
            result = getDataFromJSON(number, config, 1, "")

            if result.get("website") == "timeout":
                print("  ⚠ TIMEOUT — network error")
                continue
            if not result.get("title"):
                print("  ⚠ NOT FOUND — no data returned")
                continue

            print(f"  ✓ Success via: {result.get('website', '?')}")
            for key in FIELDS_TO_SHOW:
                val = result.get(key, "<missing>")
                if key == "tag" and isinstance(val, list):
                    val = ", ".join(str(t) for t in val) if val else "(empty)"
                elif key == "actor_photo" and isinstance(val, dict):
                    count = len(val)
                    val = f"({count} actors)"
                elif key == "extrafanart" and isinstance(val, list):
                    val = f"({len(val)} images)"
                if val and val != "<missing>" and val != "(empty)" and val != "()":
                    print(f"    {key:<16s} = {val}")

        except Exception as e:
            print(f"  ✗ Exception: {e}")

    print(f"\n{'='*60}")
    print("Done!")

if __name__ == "__main__":
    main()
