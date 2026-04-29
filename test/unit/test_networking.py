"""Tests for core/_net/networking.py — HTTP with proxy/retry."""
import pytest
from unittest.mock import patch, MagicMock

from core._net.networking import get_proxies, get_html, post_html
from core._config.errors import ConfigError, NetworkError


class TestGetProxies:
    def test_no_proxy_when_type_is_no(self):
        assert get_proxies("no", "127.0.0.1:8080") == {}
        assert get_proxies("no", "") == {}
        assert get_proxies("", "127.0.0.1:8080") == {}

    def test_http_proxy(self):
        result = get_proxies("http", "127.0.0.1:8080")
        assert result["http"] == "http://127.0.0.1:8080"
        assert result["https"] == "http://127.0.0.1:8080"

    def test_socks5_proxy(self):
        result = get_proxies("socks5", "proxy.example:1080")
        assert result["http"] == "socks5://proxy.example:1080"
        assert result["https"] == "socks5://proxy.example:1080"

    def test_unknown_type_fallback(self):
        assert get_proxies("unknown", "x:1") == {}


class TestGetHtml:
    def test_success_returns_text(self):
        mock_resp = MagicMock()
        mock_resp.text = "<html>ok</html>"
        mock_resp.encoding = None

        with patch("core._net.networking.get_proxy_config") as mock_cfg:
            mock_cfg.return_value = ("no", "", 5, 2)
            with patch("core._net.networking.requests.get", return_value=mock_resp) as mock_get:
                result = get_html("http://example.com")

        assert result == "<html>ok</html>"
        mock_get.assert_called_once()

    def test_retry_then_raises_network_error(self):
        with patch("core._net.networking.get_proxy_config") as mock_cfg:
            mock_cfg.return_value = ("no", "", 5, 2)
            with patch("core._net.networking.requests.get", side_effect=Exception("timeout")):
                with pytest.raises(NetworkError, match="failed after 2 retries"):
                    get_html("http://example.com")

    def test_proxy_config_error_raises_config_error(self):
        with patch("core._net.networking.get_proxy_config", side_effect=Exception("bad config")):
            with pytest.raises(ConfigError, match="Proxy config error"):
                get_html("http://example.com")

    def test_uses_proxies(self):
        mock_resp = MagicMock()
        mock_resp.text = "ok"
        mock_resp.encoding = None

        with patch("core._net.networking.get_proxy_config") as mock_cfg:
            mock_cfg.return_value = ("http", "proxy:8080", 10, 1)
            with patch("core._net.networking.requests.get", return_value=mock_resp) as mock_get:
                get_html("http://example.com")
                # verify proxies passed through
                _, kwargs = mock_get.call_args
                assert kwargs["proxies"] == {
                    "http": "http://proxy:8080",
                    "https": "http://proxy:8080",
                }


class TestPostHtml:
    def test_success_returns_text(self):
        mock_resp = MagicMock()
        mock_resp.text = "posted"
        mock_resp.encoding = None

        with patch("core._net.networking.get_proxy_config") as mock_cfg:
            mock_cfg.return_value = ("no", "", 5, 1)
            with patch("core._net.networking.requests.post", return_value=mock_resp) as mock_post:
                result = post_html("http://example.com", {"key": "val"})

        assert result == "posted"
        mock_post.assert_called_once()

    def test_retry_then_raises_network_error(self):
        with patch("core._net.networking.get_proxy_config") as mock_cfg:
            mock_cfg.return_value = ("no", "", 5, 1)
            with patch("core._net.networking.requests.post", side_effect=Exception("fail")):
                with pytest.raises(NetworkError, match="POST to http://example.com failed"):
                    post_html("http://example.com", {"key": "val"})

    def test_proxy_config_error_raises_config_error(self):
        with patch("core._net.networking.get_proxy_config", side_effect=Exception("bad")):
            with pytest.raises(ConfigError):
                post_html("http://example.com", {})
