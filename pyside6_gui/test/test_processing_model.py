"""Tests for ProcessingModel — skeleton and state properties."""
import pytest
from PySide6.QtCore import QObject
from PySide6.QtTest import QSignalSpy

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from processing_model import ProcessingModel


class TestProcessingModelSkeleton:
    """ProcessingModel 骨架测试"""

    def test_creates_without_error(self, qt_app):
        """ProcessingModel 应该能正常创建。"""
        model = ProcessingModel()
        assert model is not None

    def test_is_processing_initial_false(self, qt_app):
        """初始状态 isProcessing 应为 False。"""
        model = ProcessingModel()
        assert model.isProcessing is False

    def test_is_processing_setter_emits_signal(self, qt_app):
        """设置 isProcessing 应触发 isProcessingChanged 信号。"""
        model = ProcessingModel()
        spy = QSignalSpy(model.isProcessingChanged)
        model.isProcessing = True
        assert spy.count() == 1
        assert spy.at(0)[0] is True

    def test_is_processing_toggle(self, qt_app):
        """isProcessing 应该能在 True/False 之间切换。"""
        model = ProcessingModel()
        assert model.isProcessing is False

        model.isProcessing = True
        assert model.isProcessing is True

        model.isProcessing = False
        assert model.isProcessing is False

    def test_stop_slot_exists(self, qt_app):
        """stop() Slot 应该存在且可调用。"""
        model = ProcessingModel()
        model.stop()

    def test_stop_requests_flag(self, qt_app):
        """stop() 应设置内部停止标志。"""
        model = ProcessingModel()
        model.stop()
        assert model._stop_requested is True

    def test_reset_stop_flag(self, qt_app):
        """_reset_stop_flag 应清除停止标志。"""
        model = ProcessingModel()
        model.stop()
        assert model._stop_requested is True
        model._reset_stop_flag()
        assert model._stop_requested is False

    def test_log_message_signal(self, qt_app):
        """logMessage 信号应能正常发射。"""
        model = ProcessingModel()
        spy = QSignalSpy(model.logMessage)
        model._emit_log("INFO", "test message")
        assert spy.count() == 1
        assert spy.at(0)[0] == "INFO"
        assert spy.at(0)[1] == "test message"

    def test_progress_signal(self, qt_app):
        """progressChanged 信号应能正常发射。"""
        model = ProcessingModel()
        spy = QSignalSpy(model.progressChanged)
        model._emit_progress(0.5)
        assert spy.count() == 1
        assert spy.at(0)[0] == 0.5

    def test_movie_processed_signal(self, qt_app):
        """movieProcessed 信号应能正常发射。"""
        model = ProcessingModel()
        spy = QSignalSpy(model.movieProcessed)
        model.movieProcessed.emit("SSIS-123", True)
        assert spy.count() == 1
        assert spy.at(0)[0] == "SSIS-123"
        assert spy.at(0)[1] is True

    def test_batch_progress_signal(self, qt_app):
        """batchProgress 信号应能正常发射。"""
        model = ProcessingModel()
        spy = QSignalSpy(model.batchProgress)
        model.batchProgress.emit(5, 10)
        assert spy.count() == 1
        assert spy.at(0)[0] == 5
        assert spy.at(0)[1] == 10

    def test_processing_finished_signal(self, qt_app):
        """processingFinished 信号应能正常发射。"""
        model = ProcessingModel()
        spy = QSignalSpy(model.processingFinished)
        model.processingFinished.emit(8, 1, 1)
        assert spy.count() == 1
        assert spy.at(0)[0] == 8
        assert spy.at(0)[1] == 1
        assert spy.at(0)[2] == 1
