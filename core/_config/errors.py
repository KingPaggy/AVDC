"""Custom exceptions for AVDC core modules."""


class AVDCError(Exception):
    """Base exception for all AVDC errors."""
    pass


class ConfigError(AVDCError):
    """Configuration file is missing or malformed."""
    pass


class ScrapingError(AVDCError):
    """A scraper failed to retrieve data."""
    def __init__(self, source: str, number: str, message: str = ""):
        self.source = source
        self.number = number
        self.message = message or f"Scraping failed for {number} from {source}"
        super().__init__(self.message)


class NetworkError(AVDCError):
    """Network request failed after retries."""
    pass


class ImageError(AVDCError):
    """Image processing operation failed."""
    pass


class FileError(AVDCError):
    """File system operation failed."""
    pass
