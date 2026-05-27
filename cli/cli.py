#!/usr/bin/env python3
"""Standalone CLI for AVDC core — no PyQt5 dependency.

Usage:
    uv run python cli.py --path /path/to/movies
    uv run python cli.py --path /path/to/movies --main-mode organize
    uv run python cli.py --path /path/to/movies --site javbus
    uv run python cli.py --path /path/to/movies --dry-run
    uv run python cli.py --single /path/to/movie.mp4 --number ABC-123
    uv run python cli.py --path /path/to/movies --json-output
    uv run python cli.py config list
    uv run python cli.py config get website
    uv run python cli.py config set website javdb
    uv run python cli.py emby list-actors --mode without-avatar
    uv run python cli.py emby check-connection
    uv run python cli.py organize --path /path/to/movies
    uv run python cli.py poster-crop /path/to/thumb.jpg --output poster.jpg
"""
import argparse
import csv
import io
import json
import logging
import os
import re
import sys
import time
from datetime import datetime

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

CLI_VERSION = "0.2.0"


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------

def _dry_run_batch(movie_path: str, scraper_mode: int, config: AppConfig, json_output: bool) -> None:
    """Scan files, scrape metadata, print to stdout. No file I/O."""
    import logging as _logging

    from core._files.file_utils import movie_lists, getNumber
    from core._scraper.scrape_pipeline import getDataFromJSON

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


# ---------------------------------------------------------------------------
# File filtering
# ---------------------------------------------------------------------------

def _filter_movie_list(
    movie_list: list[str],
    config: AppConfig,
    number_pattern: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[str]:
    """Filter movie files by number pattern, size, and modification date."""
    from core._files.file_utils import getNumber

    filtered = movie_list

    if number_pattern:
        regex = re.compile(number_pattern)
        filtered = [
            f for f in filtered
            if (num := getNumber(f, config.string)) and regex.search(num)
        ]

    if min_size is not None:
        filtered = [f for f in filtered if os.path.getsize(f) >= min_size]

    if max_size is not None:
        filtered = [f for f in filtered if os.path.getsize(f) <= max_size]

    if since:
        cutoff = datetime.strptime(since, "%Y-%m-%d").timestamp()
        filtered = [f for f in filtered if os.path.getmtime(f) >= cutoff]

    if until:
        cutoff = datetime.strptime(until, "%Y-%m-%d").timestamp()
        filtered = [f for f in filtered if os.path.getmtime(f) <= cutoff]

    return filtered


def _parse_size(value: str) -> int:
    """Parse size string like '100M', '1G', '500000' into bytes."""
    value = value.strip().upper()
    if value.endswith("G"):
        return int(float(value[:-1]) * 1024 * 1024 * 1024)
    if value.endswith("M"):
        return int(float(value[:-1]) * 1024 * 1024)
    if value.endswith("K"):
        return int(float(value[:-1]) * 1024)
    return int(value)


# ---------------------------------------------------------------------------
# Callbacks factory
# ---------------------------------------------------------------------------

def _make_callbacks(
    json_output: bool = False,
    quiet: bool = False,
    verbose: bool = False,
    record_results: bool = False,
):
    """Create (on_log, on_progress, on_success, on_failure, results_list) callbacks."""
    results: list[dict] = [] if record_results else None

    def _emit(event_type: str, **kwargs):
        obj = {"type": event_type, **kwargs}
        print(json.dumps(obj, ensure_ascii=False), flush=True)

    if json_output:
        def on_log(msg: str) -> None:
            _emit("log", msg=msg)
        def on_progress(current: int, total: int, filepath: str) -> None:
            _emit("progress", current=current, total=total, file=filepath)
        def on_success(filepath: str, suffix: str) -> None:
            _emit("success", file=filepath, suffix=suffix)
            if results is not None:
                results.append({"file": filepath, "suffix": suffix, "status": "success"})
        def on_failure(filepath: str, reason: str, error: Exception) -> None:
            _emit("failure", file=filepath, reason=str(reason), error=str(error))
            if results is not None:
                results.append({"file": filepath, "reason": str(reason), "status": "failed"})
    elif quiet:
        def on_log(msg: str) -> None:
            pass
        def on_progress(current: int, total: int, filepath: str) -> None:
            pass
        def on_success(filepath: str, suffix: str) -> None:
            pass
        def on_failure(filepath: str, reason: str, error: Exception) -> None:
            logger.info(f"[FAIL] {filepath}: {reason}")
            if results is not None:
                results.append({"file": filepath, "reason": str(reason), "status": "failed"})
    else:
        _debug_set = False
        def on_log(msg: str) -> None:
            nonlocal _debug_set
            if verbose and not _debug_set:
                _debug_set = True
                logger.setLevel(logging.DEBUG)
                for handler in logger.handlers:
                    if handler.name == "console":
                        handler.setLevel(logging.DEBUG)
            logger.info(msg)
        def on_progress(current: int, total: int, filepath: str) -> None:
            pct = int(current / total * 100)
            print(f"\r[{pct}%] {current}/{total} — {filepath}", end="", file=sys.stderr)
        def on_success(filepath: str, suffix: str) -> None:
            print(f"\n[OK] {filepath} → {suffix}")
            if results is not None:
                results.append({"file": filepath, "suffix": suffix, "status": "success"})
        def on_failure(filepath: str, reason: str, error: Exception) -> None:
            print(f"\n[FAIL] {filepath}: {reason} ({error})")
            if results is not None:
                results.append({"file": filepath, "reason": str(reason), "status": "failed"})

    return on_log, on_progress, on_success, on_failure, results


# ---------------------------------------------------------------------------
# Subcommand: config
# ---------------------------------------------------------------------------

def _cmd_config(args, config: AppConfig):
    """Handle config subcommand."""
    if args.config_action == "list":
        for section, key, value in config.all_fields():
            print(f"{section}.{key} = {value}")
    elif args.config_action == "get":
        value = config.get_field(args.field)
        if value is not None:
            print(value)
        else:
            print(f"Unknown field: {args.field}", file=sys.stderr)
            sys.exit(1)
    elif args.config_action == "set":
        if not config.set_field(args.field, args.value):
            print(f"Failed to set field: {args.field} = {args.value}", file=sys.stderr)
            sys.exit(1)
        config.to_ini(args.config_file)
        print(f"Set {args.field} = {args.value} (saved to {args.config_file})")
    elif args.config_action == "reset":
        defaults = AppConfig()
        for section, key, _ in config.all_fields():
            field_name = config._resolve_field(f"{section}.{key}")
            if field_name:
                setattr(config, field_name, getattr(defaults, field_name))
        config.to_ini(args.config_file)
        print(f"Reset all config to defaults (saved to {args.config_file})")


# ---------------------------------------------------------------------------
# Subcommand: emby
# ---------------------------------------------------------------------------

def _cmd_emby(args, config: AppConfig):
    """Handle emby subcommand."""
    from core._services.emby_client import get_actor_list, list_actors, find_and_upload_pictures

    emby_url = getattr(args, "url", None) or config.emby_url
    api_key = getattr(args, "api_key", None) or config.api_key
    if not emby_url or not api_key:
        print("Error: Emby URL and API key required. Set in config.ini or use --url/--api-key.", file=sys.stderr)
        sys.exit(1)

    if args.emby_action == "check-connection":
        import requests
        try:
            resp = requests.get(
                f"{emby_url}/Users?api_key={api_key}",
                timeout=10,
            )
            if resp.status_code == 200:
                users = resp.json()
                print(f"Connected. {len(users)} user(s): {', '.join(u.get('Name', '?') for u in users)}")
            else:
                print(f"Connection failed: HTTP {resp.status_code}", file=sys.stderr)
                sys.exit(1)
        except Exception as e:
            print(f"Connection failed: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.emby_action == "list-actors":
        mode = getattr(args, "mode", "without-avatar")
        actor_names = get_actor_list(emby_url, api_key)
        if mode == "without-avatar":
            actors = list_actors(emby_url, api_key, actor_names)
            no_pic = [a for a in actors if not a.get("Image")]
            print(f"Actors without avatars: {len(no_pic)} / {len(actors)}")
            for a in no_pic:
                print(f"  {a.get('Name', 'unknown')}")
        elif mode == "all":
            actors = list_actors(emby_url, api_key, actor_names)
            print(f"Total actors: {len(actors)}")
            for a in actors:
                has_pic = "Yes" if a.get("Image") else "No"
                print(f"  [{has_pic}] {a.get('Name', 'unknown')}")
        elif mode == "with-avatar":
            actors = list_actors(emby_url, api_key, actor_names)
            with_pic = [a for a in actors if a.get("Image")]
            print(f"Actors with avatars: {len(with_pic)} / {len(actors)}")
            for a in with_pic:
                print(f"  {a.get('Name', 'unknown')}")

    elif args.emby_action == "upload-photos":
        actor_dir = getattr(args, "actor_dir", "./Actor")
        print(f"Scanning actor directory: {actor_dir}")
        find_and_upload_pictures(emby_url, api_key, actor_dir)
        print("Upload complete.")


# ---------------------------------------------------------------------------
# Subcommand: organize
# ---------------------------------------------------------------------------

def _cmd_organize(args, config: AppConfig):
    """Organize files without scraping (uses existing NFO metadata)."""
    config.main_mode = 2  # organize mode
    scraper_mode = 1  # doesn't matter in organize mode

    on_log, on_progress, on_success, on_failure, _ = _make_callbacks(
        json_output=args.json_output if hasattr(args, "json_output") else False,
        quiet=args.quiet if hasattr(args, "quiet") else False,
        verbose=args.verbose if hasattr(args, "verbose") else False,
    )

    engine = CoreEngine(
        config=config,
        on_log=on_log,
        on_progress=on_progress,
        on_success=on_success,
        on_failure=on_failure,
    )

    start_time = time.monotonic()
    result = engine.process_batch(args.path, scraper_mode=scraper_mode, mode=2)
    elapsed = time.monotonic() - start_time

    _print_summary(result, elapsed, args.json_output if hasattr(args, "json_output") else False)


# ---------------------------------------------------------------------------
# Subcommand: poster-crop
# ---------------------------------------------------------------------------

def _cmd_poster_crop(args, config: AppConfig):
    """Crop posters from thumb images."""
    from core._media.image_processing import cut_poster_center

    if getattr(args, "batch", False):
        from core._files.file_utils import movie_lists
        import glob

        folder = args.path
        thumb_files = glob.glob(os.path.join(folder, "*-thumb.jpg"))
        if not thumb_files:
            thumb_files = glob.glob(os.path.join(folder, "*-thumb.png"))
        if not thumb_files:
            print(f"No thumb files found in: {folder}")
            return

        print(f"Found {len(thumb_files)} thumb files, cropping posters...")
        for thumb_path in thumb_files:
            poster_path = thumb_path.replace("-thumb", "-poster")
            try:
                cut_poster_center(thumb_path, poster_path)
                print(f"  [OK] {os.path.basename(thumb_path)} -> {os.path.basename(poster_path)}")
            except Exception as e:
                print(f"  [FAIL] {os.path.basename(thumb_path)}: {e}")
    else:
        if not args.output:
            print("Error: --output required for single poster crop.", file=sys.stderr)
            sys.exit(1)
        method = getattr(args, "method", "center")
        if method == "center":
            cut_poster_center(args.input, args.output)
            print(f"Cropped poster: {args.output}")
        else:
            print(f"Unknown method: {method}", file=sys.stderr)
            sys.exit(1)


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def _print_summary(result: dict, elapsed: float, json_output: bool = False):
    """Print batch processing summary."""
    total = result["total"]
    success = result["success"]
    failed = result["failed"]
    rate = round(success / total * 100, 1) if total > 0 else 0.0

    if json_output:
        obj = {
            "type": "done", "total": total, "success": success, "failed": failed,
            "elapsed_seconds": round(elapsed, 2), "success_rate": rate,
        }
        print(json.dumps(obj, ensure_ascii=False), flush=True)
    else:
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print(f"\r{' ' * 80}\n", end="", file=sys.stderr)
        summary = f"\nSummary: {total} total, {success} success, {failed} failed ({rate}%)"
        if minutes or seconds:
            summary += f" | Elapsed: {minutes}m {seconds}s"
        print(summary)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AVDC Core CLI — JAV metadata scraper and organizer",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"AVDC CLI {CLI_VERSION}",
    )
    parser.add_argument(
        "--config", default="config.ini",
        help="Path to config.ini (default: config.ini)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # --- config subcommand ---
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("config_action", choices=["list", "get", "set", "reset"])
    config_parser.add_argument("field", nargs="?", help="Field name (e.g. 'website' or 'proxy.type')")
    config_parser.add_argument("value", nargs="?", help="New value (for 'set' action)")
    config_parser.add_argument("--config-file", default="config.ini", help=argparse.SUPPRESS)

    # --- emby subcommand ---
    emby_parser = subparsers.add_parser("emby", help="Emby integration tools")
    emby_parser.add_argument("emby_action", choices=["list-actors", "upload-photos", "check-connection"])
    emby_parser.add_argument("--url", help="Override emby_url from config")
    emby_parser.add_argument("--api-key", help="Override api_key from config")
    emby_parser.add_argument("--actor-dir", default="./Actor", help="Actor photos directory")
    emby_parser.add_argument("--mode", choices=["without-avatar", "with-avatar", "all"], default="without-avatar")

    # --- organize subcommand ---
    org_parser = subparsers.add_parser("organize", help="Organize files without scraping")
    org_parser.add_argument("--path", default=".", help="Directory containing video files")
    org_parser.add_argument("--json-output", action="store_true", help=argparse.SUPPRESS)
    org_parser.add_argument("-q", "--quiet", action="store_true", help=argparse.SUPPRESS)
    org_parser.add_argument("-v", "--verbose", action="store_true", help=argparse.SUPPRESS)

    # --- poster-crop subcommand ---
    pc_parser = subparsers.add_parser("poster-crop", help="Crop posters from thumb images")
    pc_parser.add_argument("input", help="Path to thumb image (or directory for --batch)")
    pc_parser.add_argument("--output", help="Output poster path")
    pc_parser.add_argument("--method", default="center", choices=["center"], help="Crop method")
    pc_parser.add_argument("--batch", action="store_true", help="Batch crop all thumbs in directory")

    # --- top-level arguments (batch mode defaults) ---
    parser.add_argument(
        "--path", default=".",
        help="Directory containing video files (default: current directory)",
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
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Enable debug-level console output",
    )
    parser.add_argument(
        "-q", "--quiet", action="store_true",
        help="Suppress all output except final summary",
    )

    # --- Phase 2: filtering ---
    parser.add_argument(
        "--number-pattern", metavar="REGEX",
        help="Only process files matching number regex",
    )
    parser.add_argument(
        "--min-size", metavar="BYTES",
        help="Skip files smaller than this (supports K/M/G suffixes)",
    )
    parser.add_argument(
        "--max-size", metavar="BYTES",
        help="Skip files larger than this (supports K/M/G suffixes)",
    )
    parser.add_argument(
        "--since", metavar="DATE",
        help="Only process files modified after YYYY-MM-DD",
    )
    parser.add_argument(
        "--until", metavar="DATE",
        help="Only process files modified before YYYY-MM-DD",
    )

    # --- Phase 2: retry ---
    parser.add_argument(
        "--retry-failed", type=int, default=0,
        help="Retry failed items up to N times (default: 0)",
    )
    parser.add_argument(
        "--retry-delay", type=float, default=5.0,
        help="Delay between retry attempts in seconds (default: 5)",
    )

    # --- Phase 4: concurrency ---
    parser.add_argument(
        "--concurrency", type=int, default=1,
        help="Process N files concurrently (default: 1, sequential)",
    )

    # --- Phase 5: reporting ---
    parser.add_argument(
        "--output-report", metavar="PATH",
        help="Export batch results to JSON or CSV file",
    )
    parser.add_argument(
        "--report-format", choices=["json", "csv"], default=None,
        help="Report format (auto-detected from --output-report extension if not set)",
    )

    args = parser.parse_args()

    # --- Dispatch subcommands ---
    config = AppConfig.from_ini(args.config)

    if args.command == "config":
        args.config_file = args.config
        _cmd_config(args, config)
        return

    if args.command == "emby":
        _cmd_emby(args, config)
        return

    if args.command == "organize":
        _cmd_organize(args, config)
        return

    if args.command == "poster-crop":
        _cmd_poster_crop(args, config)
        return

    # --- Batch / single mode ---
    if args.main_mode:
        config.main_mode = MAIN_MODE_MAP[args.main_mode]
    elif args.mode is not None:
        config.main_mode = args.mode

    scraper_mode = site_to_scraper_mode(args.site or config.website)

    record_results = args.output_report is not None
    on_log, on_progress, on_success, on_failure, results_list = _make_callbacks(
        json_output=args.json_output,
        quiet=args.quiet,
        verbose=args.verbose,
        record_results=record_results,
    )

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
            print(json.dumps({"type": "done", "result": str(result)}, ensure_ascii=False), flush=True)
        else:
            print(f"\nResult: {result}")
    else:
        # Apply file filters
        from core._files.file_utils import movie_lists, getNumber

        escape_folder = config.folders
        media_type = config.media_type
        movie_list = movie_lists(escape_folder, media_type, args.path)

        has_filters = any([args.number_pattern, args.min_size, args.max_size, args.since, args.until])
        if has_filters:
            min_size = _parse_size(args.min_size) if args.min_size else None
            max_size = _parse_size(args.max_size) if args.max_size else None
            movie_list = _filter_movie_list(
                movie_list, config,
                number_pattern=args.number_pattern,
                min_size=min_size, max_size=max_size,
                since=args.since, until=args.until,
            )
            if not args.quiet and not args.json_output:
                print(f"Filtered: {len(movie_list)} / {len(movie_lists(escape_folder, media_type, args.path))} files", file=sys.stderr)

        if not movie_list:
            if args.json_output:
                print(json.dumps({"type": "done", "total": 0, "success": 0, "failed": 0}, ensure_ascii=False), flush=True)
            else:
                print("No files to process after filtering.", file=sys.stderr)
            return

        # Batch processing with optional retry and concurrency
        if args.concurrency > 1:
            result = _run_concurrent_batch(
                engine, movie_list, scraper_mode,
                on_log, on_progress, on_success, on_failure,
                max_workers=args.concurrency,
                retry_failed=args.retry_failed,
                retry_delay=args.retry_delay,
            )
        else:
            result = _run_sequential_batch(
                engine, movie_list, scraper_mode,
                on_log, on_progress, on_success, on_failure,
                retry_failed=args.retry_failed,
                retry_delay=args.retry_delay,
            )

        elapsed = time.monotonic() - getattr(engine, "_start_time", time.monotonic())
        _print_summary(result, elapsed, args.json_output)

        # Export report
        if args.output_report:
            report_format = args.report_format or (
                "csv" if args.output_report.endswith(".csv") else "json"
            )
            _export_report(args.output_report, report_format, result, results_list)


def _run_sequential_batch(
    engine: CoreEngine,
    movie_list: list[str],
    scraper_mode: int,
    on_log, on_progress, on_success, on_failure,
    retry_failed: int = 0,
    retry_delay: float = 5.0,
) -> dict:
    """Run batch sequentially with optional retry."""
    import time as _time
    from core._files.file_utils import getNumber

    engine._start_time = _time.monotonic()
    total = len(movie_list)
    success_count = 0
    failed_files: list[str] = []

    for i, filepath in enumerate(movie_list, 1):
        number = getNumber(filepath, engine.config.string)
        if not number:
            on_failure(filepath, "no_number", ValueError("No number extracted"))
            failed_files.append(filepath)
            continue

        on_progress(i, total, filepath)
        try:
            result = engine.process_single(filepath, number, scraper_mode=scraper_mode)
            if result in ("not found", "error"):
                on_failure(filepath, result, Exception(result))
                failed_files.append(filepath)
            else:
                on_success(filepath, result)
                success_count += 1
        except Exception as e:
            on_failure(filepath, str(e), e)
            failed_files.append(filepath)

    # Retry failed items
    for attempt in range(1, retry_failed + 1):
        if not failed_files:
            break
        on_log(f"Retry attempt {attempt}/{retry_failed} for {len(failed_files)} failed items...")
        _time.sleep(retry_delay)
        remaining: list[str] = []
        for filepath in failed_files:
            number = getNumber(filepath, engine.config.string)
            if not number:
                continue
            try:
                result = engine.process_single(filepath, number, scraper_mode=scraper_mode)
                if result in ("not found", "error"):
                    remaining.append(filepath)
                else:
                    on_success(filepath, result)
                    success_count += 1
            except Exception as e:
                remaining.append(filepath)
        failed_files = remaining

    return {
        "total": total,
        "success": success_count,
        "failed": len(failed_files),
    }


def _run_concurrent_batch(
    engine: CoreEngine,
    movie_list: list[str],
    scraper_mode: int,
    on_log, on_progress, on_success, on_failure,
    max_workers: int = 3,
    retry_failed: int = 0,
    retry_delay: float = 5.0,
) -> dict:
    """Run batch concurrently with ThreadPoolExecutor."""
    import time as _time
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from core._files.file_utils import getNumber

    engine._start_time = _time.monotonic()
    total = len(movie_list)
    counter = {"success": 0, "failed": 0, "processed": 0}
    lock = threading.Lock()
    failed_files: list[str] = []

    def _process_one(filepath: str):
        number = getNumber(filepath, engine.config.string)
        if not number:
            with lock:
                counter["failed"] += 1
                counter["processed"] += 1
                on_failure(filepath, "no_number", ValueError("No number extracted"))
                failed_files.append(filepath)
                on_progress(counter["processed"], total, filepath)
            return

        try:
            result = engine.process_single(filepath, number, scraper_mode=scraper_mode)
            with lock:
                counter["processed"] += 1
                if result in ("not found", "error"):
                    counter["failed"] += 1
                    on_failure(filepath, result, Exception(result))
                    failed_files.append(filepath)
                else:
                    counter["success"] += 1
                    on_success(filepath, result)
                on_progress(counter["processed"], total, filepath)
        except Exception as e:
            with lock:
                counter["failed"] += 1
                counter["processed"] += 1
                on_failure(filepath, str(e), e)
                failed_files.append(filepath)
                on_progress(counter["processed"], total, filepath)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_process_one, f) for f in movie_list]
        for f in as_completed(futures):
            f.result()  # propagate exceptions

    # Retry failed items (sequentially to avoid rate limiting)
    for attempt in range(1, retry_failed + 1):
        if not failed_files:
            break
        on_log(f"Retry attempt {attempt}/{retry_failed} for {len(failed_files)} failed items...")
        _time.sleep(retry_delay)
        remaining: list[str] = []
        for filepath in failed_files:
            number = getNumber(filepath, engine.config.string)
            if not number:
                continue
            try:
                result = engine.process_single(filepath, number, scraper_mode=scraper_mode)
                if result in ("not found", "error"):
                    remaining.append(filepath)
                else:
                    on_success(filepath, result)
                    with lock:
                        counter["success"] += 1
                        counter["failed"] -= 1
            except Exception:
                remaining.append(filepath)
        failed_files.clear()
        failed_files.extend(remaining)

    return {
        "total": total,
        "success": counter["success"],
        "failed": counter["failed"],
    }


def _export_report(path: str, fmt: str, result: dict, results_list: list[dict] | None):
    """Export batch results to JSON or CSV."""
    report = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "total": result["total"],
        "success": result["success"],
        "failed": result["failed"],
        "items": results_list or [],
    }

    if fmt == "json":
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
    elif fmt == "csv":
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["file", "status", "suffix", "reason"])
            writer.writeheader()
            for item in report["items"]:
                writer.writerow({
                    "file": item.get("file", ""),
                    "status": item.get("status", ""),
                    "suffix": item.get("suffix", ""),
                    "reason": item.get("reason", ""),
                })
    print(f"Report saved: {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
