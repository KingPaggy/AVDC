#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test EventBus in simulated UI scenarios and edge cases.

Simulates the full lifecycle of a UI-driven workflow:
- Batch scrape start → progress → success/failure → end
- Concurrent event emission from multiple threads
- Handler exceptions don't break the bus
- Register/unregister handlers dynamically
- Empty event bus behavior
- Event data integrity across handlers
"""

import threading
import time
import unittest

from core._event.event_bus import EventBus
from core._event.events import Event, EventType


class MockUI:
    """Simulates a PyQt5 UI without Qt dependencies."""

    def __init__(self):
        self.log_messages = []
        self.progress_values = []
        self.success_items = []
        self.failures = []
        self.separators = []
        self.batch_started = False
        self.batch_ended = False
        self.lock = threading.Lock()

    def append_log(self, message: str):
        with self.lock:
            self.log_messages.append(message)

    def set_progress(self, value: int):
        with self.lock:
            self.progress_values.append(value)

    def add_success(self, count_claw, count, number, suffix):
        with self.lock:
            self.success_items.append((count_claw, count, number, suffix))

    def add_failure(self, count_claw, count, filepath, error):
        with self.lock:
            self.failures.append((count_claw, count, filepath, str(error)))

    def separator(self):
        with self.lock:
            self.separators.append(True)


def setup_ui_handlers(bus: EventBus, ui: MockUI):
    """Register all event handlers as a real UI would."""
    bus.on(EventType.LOG_INFO, lambda e: ui.append_log(e.message))
    bus.on(EventType.LOG_ERROR, lambda e: ui.append_log(e.message))
    bus.on(EventType.LOG_SEPARATOR, lambda e: ui.separator())
    bus.on(EventType.PROGRESS, lambda e: ui.set_progress(e.value))
    bus.on(EventType.BATCH_START, lambda e: setattr(ui, 'batch_started', True))
    bus.on(EventType.BATCH_END, lambda e: setattr(ui, 'batch_ended', True))
    bus.on(EventType.SCRAPE_SUCCESS, lambda e: ui.add_success(
        e.count_claw, e.count, e.number, e.suffix
    ))
    bus.on(EventType.SCRAPE_FAILED, lambda e: ui.add_failure(
        e.count_claw, e.count, e.filepath, e.error
    ))


class SimulatedBatchScrapeTest(unittest.TestCase):
    """Simulate a full batch scrape workflow via EventBus."""

    def setUp(self):
        self.bus = EventBus()
        self.ui = MockUI()
        setup_ui_handlers(self.bus, self.ui)

    def tearDown(self):
        self.bus.clear()

    def test_full_batch_lifecycle(self):
        """Simulate: start → 3 movies → 2 success + 1 fail → end."""
        # Batch start
        self.bus.emit(EventType.BATCH_START, total=3)
        self.assertTrue(self.ui.batch_started)

        # Movie 1: success
        self.bus.emit(EventType.LOG_INFO, message="[!] - 1 - 33.33% - [1/3] -")
        self.bus.emit(EventType.LOG_INFO, message="[!]Making Data for [video1.mp4], number [SSIS-123]")
        self.bus.emit(EventType.SCRAPE_SUCCESS,
                      count_claw=1, count=1, number="SSIS-123", suffix="-C")
        self.bus.emit(EventType.LOG_SEPARATOR)
        self.bus.emit(EventType.PROGRESS, value=33)

        # Movie 2: success
        self.bus.emit(EventType.LOG_INFO, message="[!] - 1 - 66.66% - [2/3] -")
        self.bus.emit(EventType.LOG_INFO, message="[!]Making Data for [video2.mp4], number [ABP-456]")
        self.bus.emit(EventType.SCRAPE_SUCCESS,
                      count_claw=1, count=2, number="ABP-456", suffix="")
        self.bus.emit(EventType.LOG_SEPARATOR)
        self.bus.emit(EventType.PROGRESS, value=66)

        # Movie 3: fail
        self.bus.emit(EventType.LOG_INFO, message="[!] - 1 - 100% - [3/3] -")
        self.bus.emit(EventType.LOG_INFO, message="[!]Making Data for [unknown.mp4], number [???]")
        self.bus.emit(EventType.LOG_ERROR, message="[-]Movie Data not found!")
        self.bus.emit(EventType.SCRAPE_FAILED,
                      count_claw=1, count=3, filepath="unknown.mp4", error="not found")
        self.bus.emit(EventType.LOG_SEPARATOR)
        self.bus.emit(EventType.PROGRESS, value=100)

        # Batch end
        self.bus.emit(EventType.BATCH_END, stats={"total": 3, "success": 2, "failed": 1})

        # Verify UI state
        self.assertTrue(self.ui.batch_started)
        self.assertTrue(self.ui.batch_ended)
        self.assertEqual(len(self.ui.success_items), 2)
        self.assertEqual(self.ui.success_items[0], (1, 1, "SSIS-123", "-C"))
        self.assertEqual(self.ui.success_items[1], (1, 2, "ABP-456", ""))
        self.assertEqual(len(self.ui.failures), 1)
        self.assertEqual(self.ui.failures[0], (1, 3, "unknown.mp4", "not found"))
        self.assertEqual(len(self.ui.separators), 3)
        self.assertEqual(self.ui.progress_values, [33, 66, 100])

    def test_log_messages_collected(self):
        """All log messages should be captured in order."""
        messages = [
            "[+]Find 5 movies",
            "[!] - 1 - 20% - [1/5] -",
            "[!] - 1 - 40% - [2/5] -",
            "[+]All finished!!!",
        ]
        for msg in messages:
            self.bus.emit(EventType.LOG_INFO, message=msg)

        self.assertEqual(self.ui.log_messages, messages)


class ConcurrentEventTest(unittest.TestCase):
    """Test EventBus under concurrent event emission."""

    def setUp(self):
        self.bus = EventBus()
        self.collected = []
        self.lock = threading.Lock()
        self.bus.on(EventType.LOG_INFO, lambda e: self._collect(e.message))
        self.bus.on(EventType.PROGRESS, lambda e: self._collect(e.value))

    def tearDown(self):
        self.bus.clear()

    def _collect(self, value):
        with self.lock:
            self.collected.append(value)

    def test_concurrent_emit_same_type(self):
        """100 threads emitting LOG_INFO concurrently."""
        threads = []
        for i in range(100):
            t = threading.Thread(target=self.bus.emit,
                                 args=(EventType.LOG_INFO,),
                                 kwargs={"message": f"msg-{i}"})
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.collected), 100)

    def test_concurrent_emit_different_types(self):
        """Multiple threads emitting different event types."""
        self.bus.on(EventType.SCRAPE_SUCCESS, lambda e: self._collect(("ok", e.number)))
        self.bus.on(EventType.SCRAPE_FAILED, lambda e: self._collect(("fail", e.filepath)))

        def emitter(start, count):
            for i in range(count):
                if i % 2 == 0:
                    self.bus.emit(EventType.SCRAPE_SUCCESS, number=f"SSIS-{start+i}")
                else:
                    self.bus.emit(EventType.SCRAPE_FAILED, filepath=f"file{start+i}.mp4")

        threads = [threading.Thread(target=emitter, args=(i * 50, 50)) for i in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(self.collected), 200)  # 4 * 50

    def test_concurrent_register_and_emit(self):
        """Registering handlers while emitting events."""
        results = []

        def registrar():
            for i in range(100):
                self.bus.on(EventType.LOG_INFO, lambda e: results.append(i))

        def emitter():
            for _ in range(100):
                self.bus.emit(EventType.LOG_INFO, message="x")

        t1 = threading.Thread(target=registrar)
        t2 = threading.Thread(target=emitter)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Should not crash; exact count depends on timing
        self.assertGreater(len(results), 0)


class HandlerExceptionTest(unittest.TestCase):
    """Test that handler exceptions don't break the bus."""

    def setUp(self):
        self.bus = EventBus()
        self.results = []

    def tearDown(self):
        self.bus.clear()

    def test_one_handler_fails_others_succeed(self):
        """Handler 1 raises, Handler 2 should still receive the event."""
        self.bus.on(EventType.LOG_INFO, lambda e: 1 / 0)  # will fail
        self.bus.on(EventType.LOG_INFO, lambda e: self.results.append("ok"))

        self.bus.emit(EventType.LOG_INFO, message="test")
        self.assertEqual(self.results, ["ok"])

    def test_all_handlers_fail(self):
        """All handlers raise exceptions, bus should not crash."""
        self.bus.on(EventType.LOG_INFO, lambda e: ValueError())
        self.bus.on(EventType.LOG_INFO, lambda e: KeyError())

        # Should not raise
        self.bus.emit(EventType.LOG_INFO, message="x")

    def test_handler_fails_then_recovered(self):
        """Handler fails on first call, succeeds on second."""
        call_count = [0]

        def flaky_handler(e):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("first call fails")
            self.results.append("recovered")

        self.bus.on(EventType.LOG_INFO, flaky_handler)

        self.bus.emit(EventType.LOG_INFO, message="first")
        self.assertEqual(self.results, [])

        self.bus.emit(EventType.LOG_INFO, message="second")
        self.assertEqual(self.results, ["recovered"])


class DynamicHandlerTest(unittest.TestCase):
    """Test dynamic handler registration/unregistration."""

    def setUp(self):
        self.bus = EventBus()
        self.results = []

    def tearDown(self):
        self.bus.clear()

    def test_off_stops_receiving(self):
        """Unregistering a handler should stop it from receiving events."""
        handler = lambda e: self.results.append(1)
        self.bus.on(EventType.LOG_INFO, handler)
        self.bus.emit(EventType.LOG_INFO, message="a")
        self.assertEqual(self.results, [1])

        self.bus.off(EventType.LOG_INFO, handler)
        self.bus.emit(EventType.LOG_INFO, message="b")
        self.assertEqual(self.results, [1])  # no new entry

    def test_off_unknown_handler(self):
        """Unregistering a handler that was never registered should not crash."""
        self.bus.off(EventType.LOG_INFO, lambda e: None)

    def test_off_unknown_event_type(self):
        """Unregistering from an unknown event type should not crash."""
        self.bus.off(EventType.PROGRESS, lambda e: None)

    def test_clear_removes_all(self):
        """clear() should remove all handlers."""
        self.bus.on(EventType.LOG_INFO, lambda e: self.results.append(1))
        self.bus.on(EventType.PROGRESS, lambda e: self.results.append(2))
        self.bus.clear()
        self.bus.emit(EventType.LOG_INFO, message="x")
        self.bus.emit(EventType.PROGRESS, value=50)
        self.assertEqual(self.results, [])

    def test_multiple_handlers_same_type(self):
        """Multiple handlers for same event type should all fire."""
        self.bus.on(EventType.LOG_INFO, lambda e: self.results.append("a"))
        self.bus.on(EventType.LOG_INFO, lambda e: self.results.append("b"))
        self.bus.on(EventType.LOG_INFO, lambda e: self.results.append("c"))
        self.bus.emit(EventType.LOG_INFO, message="x")
        self.assertEqual(self.results, ["a", "b", "c"])

    def test_emit_no_handlers(self):
        """Emitting with no handlers should not crash."""
        self.bus.emit(EventType.LOG_INFO, message="orphan")


class EventDataIntegrityTest(unittest.TestCase):
    """Test that event data is correctly passed through the bus."""

    def setUp(self):
        self.bus = EventBus()
        self.captured = []
        self.bus.on(EventType.SCRAPE_SUCCESS, lambda e: self.captured.append(e))

    def tearDown(self):
        self.bus.clear()

    def test_event_data_passthrough(self):
        """All emit kwargs should be accessible via event.attr."""
        self.bus.emit(EventType.SCRAPE_SUCCESS,
                      count_claw=1, count=5, number="SSIS-123", suffix="-C")
        self.assertEqual(len(self.captured), 1)
        event = self.captured[0]
        self.assertEqual(event.count_claw, 1)
        self.assertEqual(event.count, 5)
        self.assertEqual(event.number, "SSIS-123")
        self.assertEqual(event.suffix, "-C")
        self.assertEqual(event.type, EventType.SCRAPE_SUCCESS)

    def test_event_data_with_special_chars(self):
        """Unicode and special characters in event data."""
        self.bus.on(EventType.LOG_INFO, lambda e: self.captured.append(e))
        self.bus.emit(EventType.LOG_INFO, message="日本語テスト & < > \" '")
        self.assertEqual(len(self.captured), 1)
        self.assertEqual(self.captured[0].message, "日本語テスト & < > \" '")

    def test_event_data_with_complex_types(self):
        """Dict and list in event data."""
        self.bus.on(EventType.BATCH_END, lambda e: self.captured.append(e))
        stats = {"total": 10, "success": 8, "failed": 2}
        self.bus.emit(EventType.BATCH_END, stats=stats)
        self.assertEqual(len(self.captured), 1)
        self.assertEqual(self.captured[0].stats, stats)


if __name__ == "__main__":
    unittest.main()
