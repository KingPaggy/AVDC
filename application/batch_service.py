#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable, List

from core.file_utils import getNumber, movie_lists


@dataclass
class BatchRunStats:
    total: int = 0
    processed: int = 0
    success: int = 0
    failed: int = 0
    aborted: bool = False


@dataclass
class BatchCallbacks:
    log: Callable[[str], None]
    separator: Callable[[], None]
    set_progress: Callable[[int], None]
    on_success: Callable[[int, int, str, str], None]
    on_exception: Callable[[int, int, str, Exception], None]
    move_failed: Callable[[str, str], None]


class BatchWorkflowService:
    """Coordinate the AVDC batch workflow outside the Qt window class."""

    def run(
        self,
        *,
        count_claw: int,
        movie_path: str,
        escape_folder: str,
        movie_type: str,
        escape_string: str,
        mode: int,
        failed_folder: str,
        failed_move_enabled: bool,
        soft_link_enabled: bool,
        process_movie: Callable[[str, str, int, int], str],
        callbacks: BatchCallbacks,
        movie_list_provider: Callable[[str, str, str], List[str]] = movie_lists,
        number_extractor: Callable[[str, str], str] = getNumber,
    ) -> BatchRunStats:
        movie_list = movie_list_provider(escape_folder, movie_type, movie_path)
        stats = BatchRunStats(total=len(movie_list))

        callbacks.log(f"[+]Find {stats.total} movies")
        if stats.total == 0:
            callbacks.set_progress(100)

        if soft_link_enabled:
            callbacks.log("[!] --- Soft link mode is ENABLE! ----")

        for index, movie in enumerate(movie_list, start=1):
            stats.processed = index
            percentage = str(index / stats.total * 100)[:4] + "%" if stats.total else "100%"
            value = int(index / stats.total * 100) if stats.total else 100
            callbacks.log(
                f"[!] - {count_claw} - {percentage} - [{index}/{stats.total}] -"
            )

            try:
                movie_number = number_extractor(movie, escape_string)
                callbacks.log(
                    f"[!]Making Data for   [{movie}], the number is [{movie_number}]"
                )
                result = process_movie(movie, movie_number, mode, index)

                if result == "error":
                    stats.aborted = True
                    callbacks.separator()
                    break

                if result != "not found" and movie_number != "":
                    stats.success += 1
                    callbacks.on_success(count_claw, index, movie_number, result)

                callbacks.separator()
                callbacks.set_progress(value)
            except Exception as error_info:
                stats.failed += 1
                callbacks.on_exception(count_claw, index, movie, error_info)
                callbacks.log(f"[-]Error in AVDC_Main: {error_info}")
                if failed_move_enabled and not soft_link_enabled:
                    callbacks.move_failed(movie, failed_folder)
                callbacks.separator()
                callbacks.set_progress(value)

        if stats.total == 0 or not stats.aborted:
            callbacks.set_progress(100)
        return stats
