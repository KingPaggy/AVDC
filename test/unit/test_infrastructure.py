#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import time
import unittest

from core._event.events import Event, EventType
from core._event.event_bus import EventBus
from core._config.settings_provider import SettingsProvider
from core._models.process_result import ProcessResult, ProcessStatus


# ========================================================================
# Events & EventBus tests
# ========================================================================

class EventTests(unittest.TestCase):
    def test_event_type_enum(self):
        self.assertEqual(EventType.LOG_INFO.value, "log_info")
        self.assertEqual(EventType.PROGRESS.value, "progress")
        self.assertEqual(EventType.SCRAPE_SUCCESS.value, "scrape_success")

    def test_event_data_access(self):
        e = Event(type=EventType.LOG_INFO, data={"message": "hello"})
        self.assertEqual(e.message, "hello")

    def test_event_missing_key(self):
        e = Event(type=EventType.LOG_INFO)
        self.assertIsNone(e.nonexistent_key)

    def test_event_data_default(self):
        e = Event(type=EventType.PROGRESS)
        self.assertEqual(e.data, {})


class EventBusTests(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()

    def tearDown(self):
        self.bus.clear()

    def test_emit_calls_handler(self):
        results = []
        self.bus.on(EventType.LOG_INFO, lambda e: results.append(e.message))
        self.bus.emit(EventType.LOG_INFO, message="test")
        self.assertEqual(results, ["test"])

    def test_emit_multiple_handlers(self):
        results = []
        self.bus.on(EventType.LOG_INFO, lambda e: results.append(1))
        self.bus.on(EventType.LOG_INFO, lambda e: results.append(2))
        self.bus.emit(EventType.LOG_INFO)
        self.assertEqual(results, [1, 2])

    def test_off_removes_handler(self):
        results = []
        handler = lambda e: results.append(1)
        self.bus.on(EventType.LOG_INFO, handler)
        self.bus.off(EventType.LOG_INFO, handler)
        self.bus.emit(EventType.LOG_INFO)
        self.assertEqual(results, [])

    def test_emit_unknown_event_type(self):
        # Should not raise
        self.bus.emit(EventType.LOG_INFO)

    def test_handler_exception_does_not_break_others(self):
        results = []
        self.bus.on(EventType.LOG_INFO, lambda e: 1 / 0)  # will fail
        self.bus.on(EventType.LOG_INFO, lambda e: results.append("ok"))
        self.bus.emit(EventType.LOG_INFO)
        self.assertEqual(results, ["ok"])

    def test_clear_removes_all_handlers(self):
        results = []
        self.bus.on(EventType.LOG_INFO, lambda e: results.append(1))
        self.bus.clear()
        self.bus.emit(EventType.LOG_INFO)
        self.assertEqual(results, [])

    def test_thread_safety(self):
        """Concurrent emit/on/off should not crash."""
        results = []
        lock = threading.Lock()

        def handler(e):
            with lock:
                results.append(e.value)

        self.bus.on(EventType.PROGRESS, handler)

        def emitter():
            for _ in range(100):
                self.bus.emit(EventType.PROGRESS, value=1)

        def registrator():
            for _ in range(100):
                self.bus.on(EventType.LOG_INFO, lambda e: None)
                self.bus.off(EventType.LOG_INFO, lambda e: None)

        threads = [threading.Thread(target=emitter) for _ in range(4)]
        threads += [threading.Thread(target=registrator) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 400)


# ========================================================================
# SettingsProvider tests
# ========================================================================

class MockSettingsProvider(SettingsProvider):
    """Test double that returns configurable values."""

    def __init__(self, **kwargs):
        self._values = {
            "debug": False,
            "program_mode_move": True,
            "download_thumb": True,
            "download_poster": True,
            "download_fanart": True,
            "download_nfo": True,
            "copy_fanart": True,
            "restore_imagecut": False,
            "extrafanart": False,
            "print_enabled": True,
            "mark_config": {},
        }
        self._values.update(kwargs)

    def is_debug_enabled(self) -> bool:
        return self._values["debug"]

    def is_program_mode_move(self) -> bool:
        return self._values["program_mode_move"]

    def should_download_thumb(self) -> bool:
        return self._values["download_thumb"]

    def should_download_poster(self) -> bool:
        return self._values["download_poster"]

    def should_download_fanart(self) -> bool:
        return self._values["download_fanart"]

    def should_download_nfo(self) -> bool:
        return self._values["download_nfo"]

    def should_copy_fanart(self) -> bool:
        return self._values["copy_fanart"]

    def should_restore_imagecut(self) -> bool:
        return self._values["restore_imagecut"]

    def is_extrafanart_enabled(self) -> bool:
        return self._values["extrafanart"]

    def is_print_enabled(self) -> bool:
        return self._values["print_enabled"]

    def get_mark_config(self) -> dict:
        return self._values["mark_config"]


class SettingsProviderTests(unittest.TestCase):
    def test_mock_settings_returns_configured_values(self):
        settings = MockSettingsProvider(debug=True, download_thumb=False)
        self.assertTrue(settings.is_debug_enabled())
        self.assertFalse(settings.should_download_thumb())
        self.assertTrue(settings.should_download_poster())  # default

    def test_mark_config_returns_dict(self):
        settings = MockSettingsProvider(mark_config={"mark_size": 3})
        self.assertEqual(settings.get_mark_config()["mark_size"], 3)

    def test_all_methods_are_abstract(self):
        """Verify SettingsProvider cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            SettingsProvider()


# ========================================================================
# ProcessResult tests
# ========================================================================

class ProcessResultTests(unittest.TestCase):
    def test_success_result_has_all_fields(self):
        json_data = {
            "title": "Movie", "number": "SSIS-123",
            "actor": "Actor A", "release": "2024-01-01",
            "studio": "Studio", "website": "javbus",
        }
        result = ProcessResult.success_result(
            "/input/SSIS-123.mp4", "SSIS-123", json_data,
            "/output/SSIS-123", suffix="-C",
        )
        self.assertTrue(result.success)
        self.assertEqual(result.status, ProcessStatus.SUCCESS)
        self.assertEqual(result.title, "Movie")
        self.assertEqual(result.output_dir, "/output/SSIS-123")
        self.assertEqual(result.suffix, "-C")
        self.assertEqual(result.source_site, "javbus")
        self.assertEqual(result.poster_path, "/output/SSIS-123/SSIS-123-poster.jpg")

    def test_failed_result(self):
        result = ProcessResult.failed_result(
            "/input/unknown.mp4", "UNKNOWN",
            "Movie Data not found", "/output/failed",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, ProcessStatus.FAILED_NOT_FOUND)
        self.assertEqual(result.error, "Movie Data not found")
        self.assertEqual(result.failed_dir, "/output/failed")

    def test_failed_result_default_status(self):
        result = ProcessResult.failed_result("/input/x.mp4", "X", "error")
        self.assertEqual(result.status, ProcessStatus.FAILED_NOT_FOUND)

    def test_success_property(self):
        ok = ProcessResult(ProcessStatus.SUCCESS, "x", "1")
        fail = ProcessResult(ProcessStatus.FAILED_TIMEOUT, "x", "1")
        self.assertTrue(ok.success)
        self.assertFalse(fail.success)

    def test_empty_json_defaults(self):
        result = ProcessResult.success_result("x", "1", {}, "/out")
        self.assertEqual(result.title, "")
        self.assertEqual(result.actor, "")


if __name__ == "__main__":
    unittest.main()
