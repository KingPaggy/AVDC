#!/usr/bin/env python3
"""Standalone CLI for AVDC core — no PyQt5 dependency.

Usage:
    uv run python cli.py --path /path/to/movies
    uv run python cli.py --path /path/to/movies --main-mode organize
    uv run python cli.py --path /path/to/movies --site javbus
    uv run python cli.py --path /path/to/movies --dry-run
    uv run python cli.py --single /path/to/movie.mp4 --number ABC-123
    uv run python cli.py --path /path/to/movies --json-output
"""
import argparse
import json
import os
import sys

from core._services.orchestrator import CoreEngine
from core._config.config import AppConfig
from core._config.logger import logger
from core._scraper.scraper_dispatcher import site_to_scraper_mode


MAIN_MODE_MAP = {
    "1": 1,
    "scrape": 1,
    "2": 2,
    "organize": 2,
}

SITE_CHOICES = ["all", "mgstage", "javbus", "jav321", "javdb", "fc2", "avsox", "xcity", "dmm"]


def _dry_run_batch(movie_path: str, scraper_mode: int, config: AppConfig, json_output: bool) -> None:
    """Scan files, scrape metadata, print to stdout. No file I/O."""
    import logging as _logging

    from core._files.file_utils import movie_lists, getNumber
    from core._scraper.scrape_pipeline import getDataFromJSON

    # Suppress logger output in dry-run mode to keep stdout clean
    _logging.getLogger("AVDC").setLevel(_logging.CRITICAL)

    escape_folder = config.folders
    media_type = config.media_type
    movie_list = movie_lists(escape_folder, media_type, movie_path)
    total = len(movie_list)

    if total == 0:
        print(f"No media files found in: {movie_path}", file=sys.stderr)
        return

    print(f"[dry-run] Found {total} files, scraping metadata only (no file operations)", file=sys.stderr)
    if not json_output:
        print(f"[dry-run] Scraper mode: {scraper_mode}", file=sys.stderr)
        print("-" * 60, file=sys.stderr)

    success_count = 0
    fail_count = 0

    for i, filepath in enumerate(movie_list, 1):
        number = getNumber(filepath, config.string)
        if not number:
            fail_count += 1
            if json_output:
                print(json.dumps({"file": filepath, "error": "no_number"}, ensure_ascii=False), flush=True)
            else:
                print(f"[{i}/{total}] {filepath}")
                print(f"  [SKIP] No number extracted\n")
            continue

        try:
            data = getDataFromJSON(number, config, scraper_mode, "")
        except Exception as exc:
            fail_count += 1
            if json_output:
                print(json.dumps({"file": filepath, "number": number, "error": str(exc)}, ensure_ascii=False), flush=True)
            else:
                print(f"[{i}/{total}] {filepath}")
                print(f"  [ERROR] {exc}\n")
            continue

        success_count += 1

        if json_output:
            print(json.dumps({"file": filepath, "number": number, "data": data}, ensure_ascii=False), flush=True)
        else:
            print(f"[{i}/{total}] {filepath}")
            print(f"  Number : {data.get('number', 'N/A')}")
            print(f"  Title  : {data.get('title', 'N/A')}")
            print(f"  Studio : {data.get('studio', 'N/A')}")
            print(f"  Release: {data.get('release', 'N/A')}")
            actors = data.get('actor', [])
            if isinstance(actors, list):
                actors_str = ', '.join(a for a in actors if a)
            else:
                actors_str = str(actors)
            print(f"  Actors : {actors_str}")
            print(f"  Source : {data.get('source', 'N/A')}")
            print(f"  Website: {data.get('website', 'N/A')}")
            print(f"  Score  : {data.get('score', 'N/A')}")
            outline = data.get('outline', '')
            if outline and outline not in ('N/A', ''):
                print(f"  Outline: {outline[:120]}{'...' if len(outline) > 120 else ''}")
            print()

    print("-" * 60, file=sys.stderr)
    print(f"[dry-run] Done: {success_count} succeeded, {fail_count} failed, {total} total", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="AVDC Core CLI — JAV metadata scraper and organizer",
    )
    parser.add_argument(
        "--config", default="config.ini",
        help="Path to config.ini (default: config.ini)",
    )
    parser.add_argument(
        "--path", required=True,
        help="Directory containing video files",
    )
    parser.add_argument(
        "--single",
        help="Process a single file instead of batch (provide file path)",
    )
    parser.add_argument(
        "--number", default="",
        help="Movie number override (for --single mode)",
    )
    parser.add_argument(
        "--main-mode",
        choices=sorted(MAIN_MODE_MAP.keys()),
        help="Processing mode: scrape/1 or organize/2 (default: config.ini)",
    )
    parser.add_argument(
        "--site",
        choices=SITE_CHOICES,
        help="Scraper site: all, mgstage, javbus, jav321, javdb, fc2, avsox, xcity, dmm",
    )
    parser.add_argument(
        "--mode", type=int, choices=[1, 2],
        help="Deprecated alias for --main-mode 1/2",
    )
    parser.add_argument(
        "--json-output", action="store_true",
        help="Output structured JSON lines for TUI consumption",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Scrape metadata only, print to stdout, no file operations",
    )
    args = parser.parse_args()

    config = AppConfig.from_ini(args.config)
    if args.main_mode:
        config.main_mode = MAIN_MODE_MAP[args.main_mode]
    elif args.mode is not None:
        config.main_mode = args.mode

    scraper_mode = site_to_scraper_mode(args.site or config.website)

    def _emit(event_type: str, **kwargs):
        """Emit a JSON line to stdout."""
        obj = {"type": event_type, **kwargs}
        print(json.dumps(obj, ensure_ascii=False), flush=True)

    if args.json_output:
        def on_log(msg: str) -> None:
            _emit("log", msg=msg)

        def on_progress(current: int, total: int, filepath: str) -> None:
            _emit("progress", current=current, total=total, file=filepath)

        def on_success(filepath: str, suffix: str) -> None:
            _emit("success", file=filepath, suffix=suffix)

        def on_failure(filepath: str, reason: str, error: Exception) -> None:
            _emit("failure", file=filepath, reason=str(reason), error=str(error))
    else:
        def on_log(msg: str) -> None:
            logger.info(msg)

        def on_progress(current: int, total: int, filepath: str) -> None:
            pct = int(current / total * 100)
            print(f"\r[{pct}%] {current}/{total} — {filepath}", end="", file=sys.stderr)

        def on_success(filepath: str, suffix: str) -> None:
            print(f"\n[OK] {filepath} → {suffix}")

        def on_failure(filepath: str, reason: str, error: Exception) -> None:
            print(f"\n[FAIL] {filepath}: {reason} ({error})")

    engine = CoreEngine(
        config=config,
        on_log=on_log,
        on_progress=on_progress,
        on_success=on_success,
        on_failure=on_failure,
    )

    if args.dry_run:
        _dry_run_batch(args.path, scraper_mode, config, args.json_output)
    elif args.single:
        result = engine.process_single(
            args.single,
            args.number,
            scraper_mode=scraper_mode,
        )
        if args.json_output:
            _emit("done", result=str(result))
        else:
            print(f"\nResult: {result}")
    else:
        result = engine.process_batch(args.path, scraper_mode=scraper_mode)
        if args.json_output:
            _emit("done", total=result["total"],
                  success=result["success"], failed=result["failed"])
        else:
            print(
                f"\nSummary: {result['total']} total, "
                f"{result['success']} success, {result['failed']} failed",
            )


if __name__ == "__main__":
    main()
