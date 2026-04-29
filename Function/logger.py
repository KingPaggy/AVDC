"""
Centralized logging for AVDC application.

Business modules should use: from Function.logger import logger
UI layer reads log file via QTimer polling to display in QTextBrowser.

This module has ZERO Qt dependencies.
"""
import logging
import os
from datetime import datetime


def setup_logger(
    name: str = "AVDC",
    log_dir: str = "Log",
    level: int = logging.INFO,
) -> logging.Logger:
    """Create and configure the application logger.

    Outputs to:
    - Log file (always, with date-stamped filename)
    - Console (WARNING and above)

    UI display is handled separately by polling the log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"avdc_{datetime.now().strftime('%Y%m%d')}.log")

    # File handler — always write
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler — warnings and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(file_formatter)
    logger.addHandler(console_handler)

    return logger


def get_log_file_path(log_dir: str = "Log") -> str:
    """Return the current day's log file path for UI polling."""
    return os.path.join(log_dir, f"avdc_{datetime.now().strftime('%Y%m%d')}.log")


# Module-level singleton logger — import this everywhere
logger = setup_logger()
