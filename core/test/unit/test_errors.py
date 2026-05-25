"""Tests for core/_config/errors.py — exception hierarchy."""
import pytest
from core._config.errors import (
    AVDCError, ConfigError, ScrapingError, NetworkError, ImageError, FileError,
)


class TestErrorHierarchy:
    def test_avdc_error_is_base(self):
        assert issubclass(ConfigError, AVDCError)
        assert issubclass(ScrapingError, AVDCError)
        assert issubclass(NetworkError, AVDCError)
        assert issubclass(ImageError, AVDCError)
        assert issubclass(FileError, AVDCError)

    def test_avdc_error_can_be_raised(self):
        with pytest.raises(AVDCError):
            raise AVDCError("test")

    def test_config_error(self):
        err = ConfigError("config.ini not found")
        assert str(err) == "config.ini not found"
        assert isinstance(err, AVDCError)

    def test_scraping_error_default_message(self):
        err = ScrapingError(source="javbus", number="SSNI-123")
        assert err.source == "javbus"
        assert err.number == "SSNI-123"
        assert "Scraping failed for SSNI-123 from javbus" in str(err)

    def test_scraping_error_custom_message(self):
        err = ScrapingError(source="javdb", number="FC2-123", message="parse error")
        assert str(err) == "parse error"

    def test_network_error(self):
        err = NetworkError("Connection timeout")
        assert str(err) == "Connection timeout"
        assert isinstance(err, AVDCError)

    def test_image_error(self):
        err = ImageError("Failed to crop poster")
        assert str(err) == "Failed to crop poster"

    def test_file_error(self):
        err = FileError("Permission denied")
        assert str(err) == "Permission denied"

    def test_exception_catch_order(self):
        """Specific exceptions caught before generic base."""
        with pytest.raises(NetworkError):
            try:
                raise NetworkError("fail")
            except NetworkError:
                raise
            except AVDCError:
                pytest.fail("Should not reach AVDCError catch")
