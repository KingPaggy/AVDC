"""Structured result for file processing operations."""

from dataclasses import dataclass
from enum import Enum


class ProcessStatus(Enum):
    """Outcome of processing a single video file."""

    SUCCESS = "success"
    FAILED_NOT_FOUND = "failed_not_found"
    FAILED_TIMEOUT = "failed_timeout"
    FAILED_ERROR = "failed_error"


@dataclass
class ProcessResult:
    """Complete result of processing one video file.

    Success fields: title, output_dir, suffix, source_site, actor, release,
                    studio, poster_path, thumb_path
    Failure fields: error, failed_dir
    """

    status: ProcessStatus
    filepath: str
    number: str

    # Success fields
    title: str = ""
    output_dir: str = ""
    suffix: str = ""
    source_site: str = ""

    # Failure fields
    error: str = ""
    failed_dir: str = ""

    # Metadata (populated on success)
    actor: str = ""
    release: str = ""
    studio: str = ""
    poster_path: str = ""
    thumb_path: str = ""

    @property
    def success(self) -> bool:
        return self.status == ProcessStatus.SUCCESS

    @classmethod
    def success_result(
        cls,
        filepath: str,
        number: str,
        json_data: dict,
        output_dir: str,
        suffix: str = "",
    ) -> "ProcessResult":
        """Create a success result from scraper JSON data."""
        return cls(
            status=ProcessStatus.SUCCESS,
            filepath=filepath,
            number=number,
            title=json_data.get("title", ""),
            output_dir=output_dir,
            suffix=suffix,
            source_site=json_data.get("website", ""),
            actor=str(json_data.get("actor", "")),
            release=str(json_data.get("release", "")),
            studio=str(json_data.get("studio", "")),
            poster_path=output_dir + "/" + number + "-poster.jpg",
            thumb_path=output_dir + "/" + number + "-thumb.jpg",
        )

    @classmethod
    def failed_result(
        cls,
        filepath: str,
        number: str,
        reason: str,
        failed_dir: str = "",
    ) -> "ProcessResult":
        """Create a failure result."""
        return cls(
            status=ProcessStatus.FAILED_NOT_FOUND,
            filepath=filepath,
            number=number,
            error=reason,
            failed_dir=failed_dir,
        )
