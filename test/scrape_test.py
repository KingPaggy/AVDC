#!/usr/bin/env python3
import os
import sys
import json
from configparser import ConfigParser

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config_io import get_config
from core.file_utils import getNumber, movie_lists
from core.scrape_pipeline import getDataFromJSON


def main():
    config = get_config()

    test_folder = "test"
    if not os.path.exists(test_folder):
        print(f"Error: Test folder '{test_folder}' not found!")
        print("Please add video files to the test folder and run again.")
        return

    movie_type = config.get(
        "media", "media_type", fallback=".mp4|.avi|.rmvb|.wmv|.mov|.mkv"
    )
    escape_folder = config.get("escape", "folders", fallback="failed,JAV_output")

    files = movie_lists(escape_folder, movie_type, test_folder)

    if not files:
        print(f"No video files found in '{test_folder}' folder!")
        return

    print(f"Found {len(files)} video file(s)")
    print("-" * 50)

    mode = 1

    for filepath in files:
        filename = os.path.basename(filepath)
        print(f"\nProcessing: {filename}")

        escape_string = config.get("escape", "string", fallback="")
        number = getNumber(filepath, escape_string)
        print(f"  Number: {number}")

        if not number:
            print("  ERROR: Could not extract number!")
            continue

        print("  Scraping...", end=" ", flush=True)

        try:
            json_data = getDataFromJSON(number, config, mode, "")

            if json_data.get("website") == "timeout":
                print("TIMEOUT")
                continue
            elif not json_data.get("title"):
                print("NOT FOUND")
                continue

            print("OK")
            print(f"  Title: {json_data.get('title', '')}")
            print(f"  Actor: {json_data.get('actor', '')}")
            print(f"  Studio: {json_data.get('studio', '')}")
            print(f"  Release: {json_data.get('release', '')}")
            print(f"  Runtime: {json_data.get('runtime', '')} min")
            print(f"  Source: {json_data.get('source', '')}")

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "-" * 50)
    print("Done!")


if __name__ == "__main__":
    main()
