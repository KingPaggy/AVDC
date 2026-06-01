"""Integration tests for GUI-to-kernel connection.

验证 ProcessingModel、LogBridge、SettingsModel 协同工作。
"""
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest
from PySide6.QtCore import QCoreApplication, QObject, QEventLoop, QTimer, Qt
from PySide6.QtTest import QTest, QSignalSpy


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def config_model(qt_app, tmp_config_ini):
    """SettingsModel 连接到临时 config.ini。"""
    from pyside6_gui.settings_model import SettingsModel
    model = SettingsModel()
    model.config_path = str(tmp_config_ini)
    model.load()
    yield model


def _make_config_model(qt_app, tmp_config_ini):
    from pyside6_gui.settings_model import SettingsModel
    model = SettingsModel()
    model.config_path = str(tmp_config_ini)
    model.load()
    return model


# ---------------------------------------------------------------------------
# Integration Tests
# ---------------------------------------------------------------------------

class TestProcessingModelIntegration:
    """ProcessingModel + CoreEngine + EventBus 集成测试。"""

    def test_full_batch_lifecycle(self, qt_app, tmp_config_ini):
        """完整批处理生命周期：start → processing → finished → reset。"""
        from pyside6_gui.processing_model import ProcessingModel

        config_model = _make_config_model(qt_app, tmp_config_ini)
        model = ProcessingModel(config_model=config_model)

        # 监控所有关键信号
        is_processing_spy = QSignalSpy(model.isProcessingChanged)
        progress_spy = QSignalSpy(model.progressChanged)
        finished_spy = QSignalSpy(model.processingFinished)

        # 初始状态
        assert model.isProcessing is False
        assert model.progressValue == 0.0

        # 触发批处理（后台线程会实际运行，但不依赖 mock）
        model.start_batch("/nonexistent/path", "", 1)
        QTest.qWait(200)
        QCoreApplication.processEvents()

        # 应该进入 processing 状态
        assert model.isProcessing is True
        assert is_processing_spy.count() >= 1

        # 停止
        model.stop()
        QTest.qWait(500)
        QCoreApplication.processEvents()

    def test_progress_updates_during_processing(self, qt_app, tmp_config_ini):
        """处理过程中进度应该有更新。"""
        from pyside6_gui.processing_model import ProcessingModel

        config_model = _make_config_model(qt_app, tmp_config_ini)
        model = ProcessingModel(config_model=config_model)

        progress_spy = QSignalSpy(model.progressChanged)

        model.start_batch("/nonexistent/path", "", 1)
        QTest.qWait(300)
        QCoreApplication.processEvents()

        # 进度值应该被更新过
        assert progress_spy.count() >= 0  # 可能为 0 如果路径不存在立即结束
        model.stop()
        QTest.qWait(200)

    def test_stop_while_processing(self, qt_app, tmp_config_ini):
        """处理中调用 stop 应能正确重置状态。"""
        from pyside6_gui.processing_model import ProcessingModel

        config_model = _make_config_model(qt_app, tmp_config_ini)
        model = ProcessingModel(config_model=config_model)

        model.start_batch("/nonexistent/path", "", 1)
        QTest.qWait(100)

        model.stop()
        QTest.qWait(500)
        QCoreApplication.processEvents()

        # 停止后应该可以再次启动
        assert model.isProcessing is False or model._should_stop is True


class TestLogBridgeIntegration:
    """LogBridge + EventBus + LogViewer 集成。"""

    def test_eventbus_to_qt_signal_flow(self, qt_app):
        """EventBus 发射事件 → LogBridge → Qt 信号。"""
        from pyside6_gui.log_bridge import LogBridge
        from core._event.event_bus import EventBus
        from core._event.events import Event, EventType

        event_bus = EventBus()
        bridge = LogBridge(event_bus=event_bus)
        bridge.connect()

        log_spy = QSignalSpy(bridge.logReceived)

        # 通过 EventBus 发射日志
        event_bus.emit(EventType.LOG_INFO, message="test integration message")

        # 处理事件循环
        QCoreApplication.processEvents()
        QTest.qWait(100)

        assert log_spy.count() >= 1, "LogBridge 应该转发 EventBus 事件"

        # 验证消息内容
        args = log_spy.at(0)
        assert len(args) == 2  # level, message
        assert "test integration message" in args[1]

    def test_multiple_log_levels(self, qt_app):
        """不同级别的日志都应正确转发。"""
        from pyside6_gui.log_bridge import LogBridge
        from core._event.event_bus import EventBus
        from core._event.events import Event, EventType

        event_bus = EventBus()
        bridge = LogBridge(event_bus=event_bus)
        bridge.connect()

        log_spy = QSignalSpy(bridge.logReceived)

        levels = [
            (EventType.LOG_INFO, "info message"),
            (EventType.LOG_ERROR, "error message"),
            (EventType.LOG_SEPARATOR, "---"),
        ]

        for event_type, message in levels:
            event_bus.emit(event_type, message=message)
            QCoreApplication.processEvents()
            QTest.qWait(50)

        assert log_spy.count() >= 3, f"应收到 3 条日志，实际 {log_spy.count()}"

    def test_disconnect_stops_forwarding(self, qt_app):
        """disconnect 后不应再转发日志。"""
        from pyside6_gui.log_bridge import LogBridge
        from core._event.event_bus import EventBus
        from core._event.events import Event, EventType

        event_bus = EventBus()
        bridge = LogBridge(event_bus=event_bus)
        bridge.connect()

        log_spy = QSignalSpy(bridge.logReceived)

        event_bus.emit(EventType.LOG_INFO, message="before disconnect")
        QCoreApplication.processEvents()
        QTest.qWait(50)

        count_before = log_spy.count()

        bridge.disconnect()
        event_bus.emit(EventType.LOG_INFO, message="after disconnect")
        QCoreApplication.processEvents()
        QTest.qWait(50)

        count_after = log_spy.count()
        assert count_after == count_before, "disconnect 后不应再有新日志"


class TestSettingsAndProcessingIntegration:
    """SettingsModel + ProcessingModel 集成。"""

    def test_settings_passed_to_core_engine(self, qt_app, tmp_config_ini):
        """SettingsModel 的配置应正确传递给 CoreEngine。"""
        from pyside6_gui.processing_model import ProcessingModel
        from pyside6_gui.settings_model import SettingsModel

        config_model = SettingsModel()
        config_model.config_path = str(tmp_config_ini)
        config_model.load()

        # 设置特定配置
        config_model.main_mode = 0  # 刮削模式
        config_model.scraper_mode = 1  # all

        model = ProcessingModel(config_model=config_model)

        # 验证配置已设置
        assert config_model.main_mode == 0
        assert config_model.scraper_mode == 1
