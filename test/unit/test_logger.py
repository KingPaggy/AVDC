"""Tests for Function/logger.py"""
import logging
import os
import time
import pytest


def test_setup_logger_creates_log_dir(tmp_log_dir):
    """setup_logger should create the log directory and log file."""
    # Force a fresh logger name to avoid handler duplication
    from core._config.logger import setup_logger, get_log_file_path

    test_logger = setup_logger(name="TestAVDC_Logger", log_dir=tmp_log_dir)
    test_logger.info("test message")

    log_path = get_log_file_path(log_dir=tmp_log_dir)
    assert os.path.exists(log_path)

    # Cleanup
    test_logger.handlers.clear()


def test_logger_writes_to_file(tmp_log_dir):
    """Logger should write messages to the log file."""
    from core._config.logger import setup_logger, get_log_file_path

    test_logger = setup_logger(name="TestAVDC_Write", log_dir=tmp_log_dir)
    test_logger.info("hello logger test")

    # Give the file handler a moment to flush
    time.sleep(0.1)

    log_path = get_log_file_path(log_dir=tmp_log_dir)
    with open(log_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "hello logger test" in content

    # Cleanup
    test_logger.handlers.clear()


def test_logger_format_includes_timestamp(tmp_log_dir):
    """Log file lines should include timestamp, name, level, and message."""
    from core._config.logger import setup_logger, get_log_file_path

    test_logger = setup_logger(name="TestAVDC_Format", log_dir=tmp_log_dir)
    test_logger.info("format check")

    time.sleep(0.1)

    log_path = get_log_file_path(log_dir=tmp_log_dir)
    with open(log_path, "r", encoding="utf-8") as f:
        line = f.readline().strip()

    # Format: YYYY-MM-DD HH:MM:SS - NAME - LEVEL - msg
    parts = line.split(" - ", 3)
    assert len(parts) == 4
    assert parts[1] == "TestAVDC_Format"
    assert parts[2] == "INFO"
    assert "format check" in parts[3]

    # Cleanup
    test_logger.handlers.clear()


def test_get_log_file_path(tmp_log_dir):
    """get_log_file_path should return path with today's date."""
    from core._config.logger import get_log_file_path
    from datetime import datetime

    path = get_log_file_path(log_dir=tmp_log_dir)
    today = datetime.now().strftime("%Y%m%d")
    assert today in path
    assert path.endswith(".log")
