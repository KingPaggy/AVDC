"""Tests for LogBridge — EventBus → Qt Signal 桥接。"""
import pytest
from PySide6.QtTest import QSignalSpy

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core._event.events import EventType
from log_bridge import LogBridge


class MockEventBus:
    """模拟 EventBus 用于测试。"""

    def __init__(self):
        self._handlers = {}

    def on(self, event_type, handler):
        self._handlers.setdefault(event_type, []).append(handler)

    def off(self, event_type, handler):
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]
            # 清理空列表
            if not self._handlers[event_type]:
                del self._handlers[event_type]

    def emit(self, event_type, **kwargs):
        class MockEvent:
            def __init__(self, data):
                self.data = data

            def __getattr__(self, name):
                return self.data.get(name)

        handlers = list(self._handlers.get(event_type, []))
        for handler in handlers:
            handler(MockEvent(kwargs))


class TestLogBridge:
    """LogBridge 测试"""

    def test_connects_to_event_bus(self, qt_app):
        """connect() 应订阅 EventBus 事件。"""
        bus = MockEventBus()
        bridge = LogBridge(event_bus=bus)
        bridge.connect()
        assert len(bus._handlers) == 3  # LOG_INFO, LOG_ERROR, LOG_SEPARATOR

    def test_disconnects_from_event_bus(self, qt_app):
        """disconnect() 应取消订阅。"""
        bus = MockEventBus()
        bridge = LogBridge(event_bus=bus)
        bridge.connect()
        bridge.disconnect()
        assert len(bus._handlers) == 0

    def test_forwards_log_info(self, qt_app):
        """LOG_INFO 事件应转发为 logReceived("INFO", ...)。"""
        bus = MockEventBus()
        bridge = LogBridge(event_bus=bus)
        spy = QSignalSpy(bridge.logReceived)
        bridge.connect()

        bus.emit(EventType.LOG_INFO, message="test info message")

        assert spy.count() == 1
        assert spy.at(0)[0] == "INFO"
        assert spy.at(0)[1] == "test info message"

    def test_forwards_log_error(self, qt_app):
        """LOG_ERROR 事件应转发为 logReceived("ERROR", ...)。"""
        bus = MockEventBus()
        bridge = LogBridge(event_bus=bus)
        spy = QSignalSpy(bridge.logReceived)
        bridge.connect()

        bus.emit(EventType.LOG_ERROR, message="test error message")

        assert spy.count() == 1
        assert spy.at(0)[0] == "ERROR"
        assert spy.at(0)[1] == "test error message"

    def test_forwards_log_separator(self, qt_app):
        """LOG_SEPARATOR 事件应转发为 logReceived("SEPARATOR", "---")。"""
        bus = MockEventBus()
        bridge = LogBridge(event_bus=bus)
        spy = QSignalSpy(bridge.logReceived)
        bridge.connect()

        bus.emit(EventType.LOG_SEPARATOR)

        assert spy.count() == 1
        assert spy.at(0)[0] == "SEPARATOR"
        assert spy.at(0)[1] == "---"

    def test_push_manual_log(self, qt_app):
        """push() 应直接发射日志信号。"""
        bridge = LogBridge()
        spy = QSignalSpy(bridge.logReceived)

        bridge.push("INFO", "manual message")

        assert spy.count() == 1
        assert spy.at(0)[0] == "INFO"
        assert spy.at(0)[1] == "manual message"

    def test_no_event_bus_graceful(self, qt_app):
        """没有 EventBus 时 connect/disconnect 不应报错。"""
        bridge = LogBridge(event_bus=None)
        bridge.connect()  # 不应抛出异常
        bridge.disconnect()  # 不应抛出异常
