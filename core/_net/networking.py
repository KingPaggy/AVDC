import requests
import cloudscraper
from core._config.config_io import get_proxy_config
from core._config.errors import NetworkError, ConfigError


def get_proxies(proxy_type, proxy):
    proxies = {}
    if proxy == "" or proxy_type == "" or proxy_type == "no":
        proxies = {}
    elif proxy_type == "http":
        proxies = {"http": "http://" + proxy, "https": "http://" + proxy}
    elif proxy_type == "socks5":
        proxies = {"http": "socks5://" + proxy, "https": "socks5://" + proxy}
    return proxies


def get_html_javdb(url):
    """Fetch HTML with Cloudflare bypass via cloudscraper."""
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    return response.text


def get_html(url, cookies=None):
    """Fetch HTML with proxy support and retry.

    Returns HTML text on success, "ProxyError" on failure.
    """
    try:
        proxy_type, proxy, timeout, retry_count = get_proxy_config()
    except Exception as e:
        raise ConfigError(f"Proxy config error: {e}") from e

    proxies = get_proxies(proxy_type, proxy)
    for i in range(retry_count):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/60.0.3100.0 Safari/537.36"
            }
            getweb = requests.get(
                str(url),
                headers=headers,
                timeout=timeout,
                proxies=proxies,
                cookies=cookies,
            )
            getweb.encoding = "utf-8"
            return getweb.text
        except Exception as e:
            if i == retry_count - 1:
                raise NetworkError(
                    f"Request to {url} failed after {retry_count} retries: {e}"
                ) from e

    return "ProxyError"


def post_html(url: str, query: dict):
    """POST request with proxy support and retry.

    Returns response text on success, "ProxyError" on failure.
    """
    try:
        proxy_type, proxy, timeout, retry_count = get_proxy_config()
    except Exception as e:
        raise ConfigError(f"Proxy config error: {e}") from e

    proxies = get_proxies(proxy_type, proxy)
    for i in range(retry_count):
        try:
            result = requests.post(url, data=query, proxies=proxies, timeout=timeout)
            result.encoding = "utf-8"
            return result.text
        except Exception as e:
            if i == retry_count - 1:
                raise NetworkError(
                    f"POST to {url} failed after {retry_count} retries: {e}"
                ) from e

    return "ProxyError"
