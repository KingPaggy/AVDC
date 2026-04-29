#!/usr/bin/env python3
"""Standalone CLI for AVDC core — no PyQt5 dependency.

Usage:
    uv run python cli.py --path /path/to/movies
    uv run python cli.py --path /path/to/movies --mode 2
    uv run python cli.py --single /path/to/movie.mp4 --number ABC-123
"""
import argparse
import sys

from Function.core_engine import CoreEngine
from Function.config_provider import AppConfig
from Function.logger import logger


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
        "--mode", type=int, default=1, choices=[1, 2],
        help="1=scrape mode, 2=organize mode (default: 1)",
    )
    args = parser.parse_args()

    config = AppConfig.from_ini(args.config)

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

    if args.single:
        result = engine.process_single(args.single, args.number, args.mode)
        print(f"\nResult: {result}")
    else:
        result = engine.process_batch(args.path, mode=args.mode)
        print(
            f"\nSummary: {result['total']} total, "
            f"{result['success']} success, {result['failed']} failed",
        )


if __name__ == "__main__":
    main()
