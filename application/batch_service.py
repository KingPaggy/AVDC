#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from dataclasses import dataclass
from typing import Callable, List, Optional

from core.events import EventType
from core.event_bus import EventBus
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
    """DEPRECATED — use EventBus + SettingsProvider instead."""

    log: Callable[[str], None]
    separator: Callable[[], None]
    set_progress: Callable[[int], None]
    on_success: Callable[[int, int, str, str], None]
    on_exception: Callable[[int, int, str, Exception], None]
    move_failed: Callable[[str, str], None]


class _LegacyBatchEventBusAdapter(EventBus):
    """Wrap old BatchCallbacks as an EventBus."""

    def __init__(self, callbacks: BatchCallbacks):
        super().__init__()
        self._callbacks = callbacks
        self.on(EventType.LOG_INFO, lambda e: callbacks.log(e.message))
        self.on(EventType.LOG_SEPARATOR, lambda e: callbacks.separator())
        self.on(EventType.PROGRESS, lambda e: callbacks.set_progress(e.value))
        self.on(EventType.SCRAPE_SUCCESS, lambda e: callbacks.on_success(
            e.count_claw, e.count, e.number, e.suffix
        ))
        self.on(EventType.SCRAPE_FAILED, lambda e: callbacks.on_exception(
            e.count_claw, e.count, e.filepath, e.error
        ))
        self.on(EventType.FILE_MOVED, lambda e: callbacks.move_failed(
            e.src, e.dst
        ))


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
        callbacks: Optional[BatchCallbacks] = None,
        bus: Optional[EventBus] = None,
        movie_list_provider: Callable[[str, str, str], List[str]] = movie_lists,
        number_extractor: Callable[[str, str], str] = getNumber,
    ) -> BatchRunStats:
        # Resolve bus: prefer new bus, fall back to callbacks adapter
        if bus is None and callbacks is not None:
            bus = _LegacyBatchEventBusAdapter(callbacks)
        if bus is None:
            bus = EventBus()

        return self._run_new(
            count_claw=count_claw,
            movie_path=movie_path,
            escape_folder=escape_folder,
            movie_type=movie_type,
            escape_string=escape_string,
            mode=mode,
            failed_folder=failed_folder,
            failed_move_enabled=failed_move_enabled,
            soft_link_enabled=soft_link_enabled,
            process_movie=process_movie,
            bus=bus,
            movie_list_provider=movie_list_provider,
            number_extractor=number_extractor,
        )

    def _run_new(
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
        process_movie: Callable,
        bus: EventBus,
        movie_list_provider: Callable,
        number_extractor: Callable,
    ) -> BatchRunStats:
        movie_list = movie_list_provider(escape_folder, movie_type, movie_path)
        stats = BatchRunStats(total=len(movie_list))

        bus.emit(EventType.BATCH_START, total=stats.total)
        bus.emit(EventType.LOG_INFO, message=f"[+]Find {stats.total} movies")
        if stats.total == 0:
            bus.emit(EventType.PROGRESS, value=100)

        if soft_link_enabled:
            bus.emit(EventType.LOG_INFO, message="[!] --- Soft link mode is ENABLE! ----")

        for index, movie in enumerate(movie_list, start=1):
            stats.processed = index
            percentage = str(index / stats.total * 100)[:4] + "%" if stats.total else "100%"
            value = int(index / stats.total * 100) if stats.total else 100
            bus.emit(EventType.LOG_INFO, message=f"[!] - {count_claw} - {percentage} - [{index}/{stats.total}] -")

            try:
                movie_number = number_extractor(movie, escape_string)
                bus.emit(EventType.LOG_INFO, message=f"[!]Making Data for   [{movie}], the number is [{movie_number}]")
                result = process_movie(movie, movie_number, mode, index)

                if result == "error" or (hasattr(result, "status") and getattr(result, "status", None).value == "failed_timeout"):
                    stats.aborted = True
                    bus.emit(EventType.LOG_SEPARATOR)
                    break

                if result != "not found" and movie_number != "":
                    stats.success += 1
                    if hasattr(result, "success"):
                        suffix = getattr(result, "suffix", "")
                    else:
                        suffix = result
                    bus.emit(EventType.SCRAPE_SUCCESS,
                             count_claw=count_claw, count=index,
                             number=movie_number, suffix=suffix)

                bus.emit(EventType.LOG_SEPARATOR)
                bus.emit(EventType.PROGRESS, value=value)
            except Exception as error_info:
                stats.failed += 1
                bus.emit(EventType.SCRAPE_FAILED,
                         count_claw=count_claw, count=index,
                         filepath=movie, error=str(error_info))
                bus.emit(EventType.LOG_INFO, message=f"[-]Error in AVDC_Main: {error_info}")
                if failed_move_enabled and not soft_link_enabled:
                    bus.emit(EventType.FILE_MOVED, src=movie, dst=failed_folder)
                bus.emit(EventType.LOG_SEPARATOR)
                bus.emit(EventType.PROGRESS, value=value)

        if stats.total == 0 or not stats.aborted:
            bus.emit(EventType.PROGRESS, value=100)
        bus.emit(EventType.BATCH_END, stats=stats)
        return stats
