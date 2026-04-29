"""
Core orchestrator for AVDC — the primary entry point for the scrape/organize workflow.

No Qt dependency. Accepts AppConfig for all settings. Reports via callbacks.
"""
from __future__ import annotations

import os
import re
from typing import Callable, Optional

from core.config import AppConfig
from core.logger import logger
from Function.file_ops import (
    download_thumb,
    download_small_cover,
    download_extrafanart,
    write_nfo,
    move_to_failed,
    paste_file_to_folder,
    copy_as_fanart,
    delete_thumb,
    get_disc_part,
    create_output_folder,
    resolve_naming_rule,
    clean_empty_dirs,
)
from Function.image_ops import cut_poster as _cut_poster, fix_image_size as _fix_image_size, apply_marks as _apply_marks
from core.file_utils import movie_lists, getNumber
from core.scrape_pipeline import getDataFromJSON


# Callback signatures
OnLog = Callable[[str], None]
OnProgress = Callable[[int, int, str], None]  # current, total, filepath
OnSuccess = Callable[[str, str], None]  # filepath, result_suffix
OnFailure = Callable[[str, str, Exception], None]  # filepath, reason, error


class CoreEngine:
    """Orchestrates the full scrape/organize workflow without UI references."""

    def __init__(
        self,
        config: AppConfig,
        on_log: Optional[OnLog] = None,
        on_progress: Optional[OnProgress] = None,
        on_success: Optional[OnSuccess] = None,
        on_failure: Optional[OnFailure] = None,
    ):
        self.config = config
        self.on_log = on_log or (lambda msg: logger.info(msg))
        self.on_progress = on_progress or (lambda c, t, f: None)
        self.on_success = on_success or (lambda f, s: None)
        self.on_failure = on_failure or (lambda f, r, e: None)

    # ========================================================================
    # Batch processing
    # ========================================================================

    def process_batch(
        self,
        movie_path: str,
        escape_folder: str = "",
        mode: int = 1,
    ) -> dict:
        """Process all movies in movie_path. Returns summary dict."""
        self.on_log(f"[+]Find movies in: {movie_path}")

        failed_folder = os.path.join(movie_path, self.config.failed_output_folder)
        success_folder = os.path.join(movie_path, self.config.success_output_folder)

        # Create failed folder if configured
        if self.config.failed_file_move and not os.path.exists(failed_folder):
            os.makedirs(failed_folder + "/")

        movie_list = movie_lists(escape_folder, self.config.media_type, movie_path)
        count_all = len(movie_list)
        self.on_log(f"[+]Find {count_all} movies")

        if count_all == 0:
            return {"total": 0, "success": 0, "failed": 0}

        count = 0
        success_count = 0
        failed_count = 0

        for filepath in movie_list:
            count += 1
            pct = int(count / count_all * 100)
            self.on_progress(count, count_all, filepath)
            self.on_log(
                f"[!] - {count}/{count_all} - {filepath}"
            )

            try:
                escape_string = self.config.string
                movie_number = getNumber(filepath, escape_string)
                self.on_log(f"[!]Making Data for [{filepath}], number [{movie_number}]")

                if not movie_number:
                    self.on_log("[-]Could not extract number!")
                    failed_count += 1
                    self.on_failure(filepath, "no_number", ValueError("No number"))
                    continue

                suffix = self._process_single_core(
                    filepath=filepath,
                    number=movie_number,
                    mode=mode,
                    count=count,
                    success_folder=success_folder,
                    failed_folder=failed_folder,
                )

                if suffix == "not found":
                    failed_count += 1
                elif suffix == "error":
                    self.on_log("[-]Processing error, stopping batch")
                    break
                else:
                    success_count += 1
                    self.on_success(filepath, suffix)

            except Exception as exc:
                failed_count += 1
                self.on_log(f"[-]Error: {exc}")
                self.on_failure(filepath, "exception", exc)

            # Note: move_to_failed is called within _process_single_core on failure

        # Clean empty directories
        clean_empty_dirs(movie_path)

        self.on_log("[+]All finished!!!")
        return {"total": count_all, "success": success_count, "failed": failed_count}

    # ========================================================================
    # Single file processing
    # ========================================================================

    def process_single(
        self,
        filepath: str,
        number: str,
        mode: int = 1,
        appoint_url: str = "",
    ) -> str:
        """Process a single file. Returns result suffix or 'not found'/'error'."""
        success_folder = os.path.join(
            os.path.dirname(filepath),
            self.config.success_output_folder,
        )
        failed_folder = os.path.join(
            os.path.dirname(filepath),
            self.config.failed_output_folder,
        )
        return self._process_single_core(
            filepath=filepath,
            number=number,
            mode=mode,
            count=1,
            success_folder=success_folder,
            failed_folder=failed_folder,
            appoint_url=appoint_url,
        )

    def _process_single_core(
        self,
        filepath: str,
        number: str,
        mode: int,
        count: int,
        success_folder: str,
        failed_folder: str,
        appoint_url: str = "",
    ) -> str:
        """Internal single-file processing logic."""
        leak = 0
        uncensored = 0
        cn_sub = 0
        c_word = ""
        multi_part = 0
        part = ""
        program_mode = self.config.main_mode  # 1=scrape, 2=organize

        # =================================================================== Fetch metadata
        json_data = getDataFromJSON(number, self.config, mode, appoint_url)

        # =================================================================== Check results
        if json_data.get("website") == "timeout":
            self.on_log("[-]Connect Failed! Please check your Proxy or Network!")
            move_to_failed(filepath, failed_folder, self.config)
            return "error"
        elif not json_data.get("title"):
            self.on_log("[-]Movie Data not found!")
            move_to_failed(filepath, failed_folder, self.config)
            return "not found"
        elif "http" not in json_data.get("cover", ""):
            move_to_failed(filepath, failed_folder, self.config)
            raise Exception("Cover Url is None!")
        elif json_data.get("imagecut") == 3 and "http" not in json_data.get("cover_small", ""):
            move_to_failed(filepath, failed_folder, self.config)
            raise Exception("Cover_small Url is None!")

        # =================================================================== Detect suffixes
        if "-CD" in filepath or "-cd" in filepath:
            multi_part = 1
            part = get_disc_part(filepath)

        if "-c." in filepath or "-C." in filepath or "中文" in filepath or "字幕" in filepath:
            cn_sub = 1
            c_word = "-C"

        if json_data.get("imagecut") == 3:
            uncensored = 1

        if "流出" in os.path.basename(filepath):
            leak = 1

        # =================================================================== Create folder & name
        path = create_output_folder(success_folder, json_data, self.config)
        self.on_log(f"[+]Folder : {path}")
        self.on_log(f"[+]From   : {json_data['website']}")

        number = json_data.get("number", number)
        naming_rule = resolve_naming_rule(json_data).replace("--", "-").strip("-")

        if leak == 1:
            naming_rule += "-流出"
        if multi_part == 1:
            naming_rule += part
        if cn_sub == 1:
            naming_rule += c_word

        thumb_path = os.path.join(path, naming_rule + "-thumb.jpg")
        poster_path = os.path.join(path, naming_rule + "-poster.jpg")

        # Override imagecut for uncensored poster mode
        if json_data.get("imagecut") == 3 and self.config.uncensored_poster == 1:
            json_data["imagecut"] = 0

        # =================================================================== Scrape mode
        if program_mode == 1:
            # Download thumb
            download_thumb(json_data, path, naming_rule, self.config, filepath, failed_folder)

            # Poster handling
            if self.config.poster_download:
                small_result = download_small_cover(
                    path, naming_rule, json_data, self.config, filepath, failed_folder,
                )
                if small_result == "small_cover_error":
                    json_data["imagecut"] = 0

                _cut_poster(
                    json_data["imagecut"], path, naming_rule,
                    baidu_credentials={
                        "app_id": self.config.baidu_app_id,
                        "api_key": self.config.baidu_api_key,
                        "secret_key": self.config.baidu_secret_key,
                    },
                )
                _fix_image_size(path, naming_rule)

            if self.config.fanart_download:
                copy_as_fanart(path, naming_rule)

            delete_thumb(path, naming_rule, keep_thumb=self.config.thumb_download)

            # Move file
            had_sub = paste_file_to_folder(
                filepath, path, naming_rule, failed_folder, self.config,
            )
            if had_sub:
                cn_sub = 1

            if self.config.nfo_download:
                write_nfo(path, naming_rule, cn_sub, leak, json_data, filepath, failed_folder, self.config)

            if self.config.extrafanart_download:
                download_extrafanart(json_data, path, self.config, filepath, failed_folder)

            # Add watermarks
            if self.config.thumb_mark:
                _apply_marks(thumb_path, cn_sub, leak, uncensored, {
                    "mark_size": self.config.mark_size,
                    "mark_pos": self.config.mark_pos,
                })
            if self.config.poster_mark:
                _apply_marks(poster_path, cn_sub, leak, uncensored, {
                    "mark_size": self.config.mark_size,
                    "mark_pos": self.config.mark_pos,
                })

        # =================================================================== Organize mode
        elif program_mode == 2:
            paste_file_to_folder(filepath, path, naming_rule, failed_folder, self.config)

        # Return suffix for UI display
        return part + c_word
