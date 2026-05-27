"""Tests for cli.py — standalone CLI entry point (no PyQt5)."""
import sys
import pytest
from unittest.mock import patch, MagicMock

from cli.cli import main
from core._config.config import AppConfig


def _mock_config(**overrides):
    return AppConfig(**overrides)


# ========================================================================
# Argument parsing
# ========================================================================

class TestArgumentParsing:
    """Test that argparse handles arguments correctly."""

    def test_default_config_is_loaded(self):
        """When no mode/site flags are specified, config should be loaded."""
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
        engine_kwargs = MockEngine.call_args.kwargs
        assert engine_kwargs["config"] is not None

    def test_main_mode_organize_updates_config_not_scraper_mode(self):
        """--main-mode organize should update config.main_mode only."""
        test_args = ["cli.py", "--path", "/tmp/movies", "--main-mode", "organize"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    config = _mock_config()
                    MockConfig.from_ini.return_value = config
                    instance = MockEngine.return_value
                    instance.process_single.return_value = "success"
                    with patch("core._files.file_utils.movie_lists", return_value=["/tmp/movies/test.mp4"]):
                        with patch("core._files.file_utils.getNumber", return_value="TEST-001"):
                            main()
        instance.process_single.assert_called_once()
        assert config.main_mode == 2

    def test_deprecated_mode_2_updates_main_mode_only(self):
        """--mode 2 remains a compatibility alias for organize mode."""
        test_args = ["cli.py", "--path", "/tmp/movies", "--mode", "2"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    config = _mock_config()
                    MockConfig.from_ini.return_value = config
                    instance = MockEngine.return_value
                    instance.process_single.return_value = "success"
                    with patch("core._files.file_utils.movie_lists", return_value=["/tmp/movies/test.mp4"]):
                        with patch("core._files.file_utils.getNumber", return_value="TEST-001"):
                            main()
        instance.process_single.assert_called_once()
        assert config.main_mode == 2

    def test_site_flag_selects_scraper_mode(self):
        """--site should select the scraper chain independently of main_mode."""
        test_args = ["cli.py", "--path", "/tmp/movies", "--site", "javbus"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    instance.process_single.return_value = "success"
                    with patch("core._files.file_utils.movie_lists", return_value=["/tmp/movies/test.mp4"]):
                        with patch("core._files.file_utils.getNumber", return_value="TEST-001"):
                            main()
        call_kwargs = instance.process_single.call_args.kwargs
        assert call_kwargs["scraper_mode"] == 3

    def test_config_website_selects_default_scraper_mode(self):
        """Config website is used when --site is omitted."""
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config(website="javdb")
                    instance = MockEngine.return_value
                    instance.process_single.return_value = "success"
                    with patch("core._files.file_utils.movie_lists", return_value=["/tmp/movies/test.mp4"]):
                        with patch("core._files.file_utils.getNumber", return_value="TEST-001"):
                            main()
        call_kwargs = instance.process_single.call_args.kwargs
        assert call_kwargs["scraper_mode"] == 5

    def test_single_mode_calls_process_single(self):
        """--single should call process_single instead of process_batch."""
        test_args = ["cli.py", "--path", "/tmp", "--single", "/tmp/m.mp4"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    main()
        instance.process_single.assert_called_once()
        instance.process_batch.assert_not_called()

    def test_custom_config_path(self):
        """--config should be passed to AppConfig.from_ini."""
        test_args = ["cli.py", "--config", "/custom/config.ini", "--path", "/tmp"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine"):
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
        MockConfig.from_ini.assert_called_once_with("/custom/config.ini")

    def test_number_passed_to_process_single(self):
        """--number should be passed to process_single."""
        test_args = [
            "cli.py", "--path", "/tmp",
            "--single", "/tmp/v.mp4", "--number", "ABC-123",
        ]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    main()
        instance.process_single.assert_called_once_with(
            "/tmp/v.mp4",
            "ABC-123",
            scraper_mode=1,
        )


# ========================================================================
# Callback functions
# ========================================================================

class TestCallbacks:
    """Test that callbacks produce correct output."""

    def test_on_progress_format(self, capsys):
        """progress callback should print percentage to stderr."""
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
                    on_progress = MockEngine.call_args.kwargs["on_progress"]
        on_progress(3, 10, "/tmp/movie.mp4")
        captured = capsys.readouterr()
        assert "[30%]" in captured.err
        assert "movie.mp4" in captured.err

    def test_on_success_format(self, capsys):
        """success callback should print [OK] to stdout."""
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
                    on_success = MockEngine.call_args.kwargs["on_success"]
        on_success("/tmp/movie.mp4", "-C")
        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "/tmp/movie.mp4" in captured.out

    def test_on_failure_format(self, capsys):
        """failure callback should print [FAIL] to stdout."""
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
                    on_failure = MockEngine.call_args.kwargs["on_failure"]
        on_failure("/tmp/movie.mp4", "no_number", ValueError("bad"))
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.out
        assert "no_number" in captured.out

    def test_on_log_calls_logger_info(self):
        """log callback should delegate to logger.info."""
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine") as MockEngine:
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    instance = MockEngine.return_value
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
                    on_log = MockEngine.call_args.kwargs["on_log"]
        with patch("cli.cli.logger.info") as mock_info:
            on_log("test message")
        mock_info.assert_called_once_with("test message")


# ========================================================================
# Error handling
# ========================================================================

class TestErrorHandling:
    """Test that CLI handles errors gracefully."""

    def test_main_when_called_directly(self):
        """__name__ == '__main__' guard should invoke main()."""
        test_args = ["cli.py", "--path", "/tmp"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine"):
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()

    def test_empty_directory_handled_gracefully(self, capsys):
        """When no files match filters, CLI should exit gracefully."""
        test_args = ["cli.py", "--path", "/tmp/empty"]
        with patch("sys.argv", test_args):
            with patch("cli.cli.CoreEngine"):
                with patch("cli.cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = _mock_config()
                    with patch("core._files.file_utils.movie_lists", return_value=[]):
                        main()
        captured = capsys.readouterr()
        assert "No files to process" in captured.err
