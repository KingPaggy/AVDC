"""Event definitions for the AVDC event bus.

All communication between core services and the UI layer flows through
typed events, decoupling the two sides.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    """All event types emitted by core services."""

    # Lifecycle
    PROCESSING_START = "processing_start"
    PROCESSING_END = "processing_end"

    # Logging
    LOG_INFO = "log_info"
    LOG_ERROR = "log_error"
    LOG_SEPARATOR = "log_separator"

    # Progress
    PROGRESS = "progress"

    # File operations
    FILE_MOVED = "file_moved"
    FILE_DELETED = "file_deleted"
    DIR_CREATED = "dir_created"

    # Downloads
    DOWNLOAD_START = "download_start"
    DOWNLOAD_SUCCESS = "download_success"
    DOWNLOAD_FAILED = "download_failed"

    # Image processing
    IMAGE_CUT = "image_cut"
    IMAGE_WATERMARK = "image_watermark"
    IMAGE_RESIZE = "image_resize"

    # Scrape results
    SCRAPE_SUCCESS = "scrape_success"
    SCRAPE_FAILED = "scrape_failed"

    # Batch operations
    BATCH_START = "batch_start"
    BATCH_END = "batch_end"


@dataclass
class Event:
    """Base event carrying arbitrary key-value data."""

    type: EventType
    data: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        """Allow event.key access to data fields."""
        return self.data.get(name)
