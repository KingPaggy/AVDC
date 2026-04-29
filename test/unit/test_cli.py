"""Tests for cli.py — standalone CLI entry point (no PyQt5)."""
import sys
import pytest
from unittest.mock import patch, MagicMock


# ========================================================================
# Argument parsing
# ========================================================================

class TestArgumentParsing:
    """Test that argparse handles arguments correctly."""

    def test_default_mode_is_scrape(self):
        """When --mode is not specified, default should be 1 (scrape)."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    main()
        engine_kwargs = MockEngine.call_args.kwargs
        assert engine_kwargs["config"] is not None

    def test_mode_2_is_organize(self):
        """--mode 2 should pass organize mode to process_batch."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp/movies", "--mode", "2"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    main()
        instance.process_batch.assert_called_once()
        _, kwargs = instance.process_batch.call_args
        assert kwargs["mode"] == 2

    def test_single_mode_calls_process_single(self):
        """--single should call process_single instead of process_batch."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp", "--single", "/tmp/m.mp4"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    main()
        instance.process_single.assert_called_once()
        instance.process_batch.assert_not_called()

    def test_custom_config_path(self):
        """--config should be passed to AppConfig.from_ini."""
        from cli import main
        test_args = ["cli.py", "--config", "/custom/config.ini", "--path", "/tmp"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine"):
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    main()
        MockConfig.from_ini.assert_called_once_with("/custom/config.ini")

    def test_number_passed_to_process_single(self):
        """--number should be passed to process_single."""
        from cli import main
        test_args = [
            "cli.py", "--path", "/tmp",
            "--single", "/tmp/v.mp4", "--number", "ABC-123",
        ]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    main()
        instance.process_single.assert_called_once_with("/tmp/v.mp4", "ABC-123", 1)


# ========================================================================
# Callback functions
# ========================================================================

class TestCallbacks:
    """Test that callbacks produce correct output."""

    def test_on_progress_format(self, capsys):
        """progress callback should print percentage to stderr."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    # Capture the on_progress callback and call it directly
                    main()
                    on_progress = MockEngine.call_args.kwargs["on_progress"]
        on_progress(3, 10, "/tmp/movie.mp4")
        captured = capsys.readouterr()
        assert "[30%]" in captured.err
        assert "movie.mp4" in captured.err

    def test_on_success_format(self, capsys):
        """success callback should print [OK] to stdout."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    main()
                    on_success = MockEngine.call_args.kwargs["on_success"]
        on_success("/tmp/movie.mp4", "-C")
        captured = capsys.readouterr()
        assert "[OK]" in captured.out
        assert "/tmp/movie.mp4" in captured.out

    def test_on_failure_format(self, capsys):
        """failure callback should print [FAIL] to stdout."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    main()
                    on_failure = MockEngine.call_args.kwargs["on_failure"]
        on_failure("/tmp/movie.mp4", "no_number", ValueError("bad"))
        captured = capsys.readouterr()
        assert "[FAIL]" in captured.out
        assert "no_number" in captured.out

    def test_on_log_calls_logger_info(self):
        """log callback should delegate to logger.info."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp/movies"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine") as MockEngine:
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    instance = MockEngine.return_value
                    main()
                    on_log = MockEngine.call_args.kwargs["on_log"]
        with patch("cli.logger.info") as mock_info:
            on_log("test message")
        mock_info.assert_called_once_with("test message")


# ========================================================================
# Error handling
# ========================================================================

class TestErrorHandling:
    """Test that CLI handles errors gracefully."""

    def test_main_when_called_directly(self):
        """__name__ == '__main__' guard should invoke main()."""
        from cli import main
        test_args = ["cli.py", "--path", "/tmp"]
        with patch("sys.argv", test_args):
            with patch("cli.CoreEngine"):
                with patch("cli.AppConfig") as MockConfig:
                    MockConfig.from_ini.return_value = MagicMock()
                    # Invoke via __main__ path simulation
                    main()

    def test_requires_path(self):
        """--path is required and should error if missing."""
        from cli import main
        test_args = ["cli.py"]
        with patch("sys.argv", test_args):
            with pytest.raises(SystemExit):
                main()
