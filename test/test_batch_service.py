#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest

from application.batch_service import BatchCallbacks, BatchWorkflowService


class BatchWorkflowServiceTests(unittest.TestCase):
    def test_run_batches_movies_and_tracks_results(self):
        events = []

        def log(message):
            events.append(("log", message))

        def separator():
            events.append(("separator", None))

        def set_progress(value):
            events.append(("progress", value))

        def on_success(count_claw, count, movie_number, suffix):
            events.append(("success", count_claw, count, movie_number, suffix))

        def on_exception(count_claw, count, filepath, error_info):
            events.append(("exception", count_claw, count, filepath, str(error_info)))

        def move_failed(filepath, failed_folder):
            events.append(("move_failed", filepath, failed_folder))

        callbacks = BatchCallbacks(
            log=log,
            separator=separator,
            set_progress=set_progress,
            on_success=on_success,
            on_exception=on_exception,
            move_failed=move_failed,
        )

        def movie_list_provider(escape_folder, movie_type, movie_path):
            return ["/tmp/a.mp4", "/tmp/b.mp4"]

        def number_extractor(filepath, escape_string):
            return "ABP-123" if filepath.endswith("a.mp4") else "ABP-456"

        def process_movie(filepath, movie_number, mode, count):
            return "-C" if filepath.endswith("a.mp4") else "error"

        service = BatchWorkflowService()
        stats = service.run(
            count_claw=2,
            movie_path="/tmp",
            escape_folder="",
            movie_type=".mp4",
            escape_string="",
            mode=1,
            failed_folder="/tmp/failed",
            failed_move_enabled=True,
            soft_link_enabled=True,
            process_movie=process_movie,
            callbacks=callbacks,
            movie_list_provider=movie_list_provider,
            number_extractor=number_extractor,
        )

        self.assertEqual(stats.total, 2)
        self.assertEqual(stats.processed, 2)
        self.assertEqual(stats.success, 1)
        self.assertTrue(stats.aborted)
        self.assertIn(("success", 2, 1, "ABP-123", "-C"), events)
        self.assertIn(("progress", 50), events)
        self.assertNotIn(("progress", 100), events)


if __name__ == "__main__":
    unittest.main()
