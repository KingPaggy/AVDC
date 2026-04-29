"""Tests for Function/config_provider.py"""
import os
import pytest
from core._config.config import AppConfig


def test_from_ini_reads_all_fields(tmp_config_ini):
    """AppConfig.from_ini should read all fields from config.ini."""
    cfg = AppConfig.from_ini(path=tmp_config_ini)
    assert cfg.main_mode == 1
    assert cfg.soft_link == 0
    assert cfg.failed_file_move == 1
    assert cfg.website == "all"
    assert cfg.success_output_folder == "JAV_output"
    assert cfg.failed_output_folder == "failed"
    assert cfg.proxy_type == "no"
    assert cfg.timeout == 5
    assert cfg.retry == 3
    assert cfg.folder_name == "actor/number"
    assert cfg.naming_media == "number-title"
    assert cfg.naming_file == "number"
    assert cfg.emby_url == ""
    assert cfg.api_key == ""
    assert cfg.nfo_download == 1
    assert cfg.baidu_app_id == ""


def test_to_ini_writes_all_fields(tmp_dir, tmp_config_ini):
    """AppConfig.to_ini should write all fields, and round-trip should be consistent."""
    # Read
    cfg = AppConfig.from_ini(path=tmp_config_ini)
    # Modify some fields
    cfg.main_mode = 2
    cfg.website = "javbus"
    cfg.proxy_type = "socks5"
    cfg.proxy = "127.0.0.1:1080"
    cfg.emby_url = "localhost:8096"
    cfg.baidu_app_id = "12345"

    # Write to new file
    out_path = os.path.join(tmp_dir, "output_config.ini")
    cfg.to_ini(path=out_path)

    # Read back
    cfg2 = AppConfig.from_ini(path=out_path)
    assert cfg2.main_mode == 2
    assert cfg2.website == "javbus"
    assert cfg2.proxy_type == "socks5"
    assert cfg2.proxy == "127.0.0.1:1080"
    assert cfg2.emby_url == "localhost:8096"
    assert cfg2.baidu_app_id == "12345"


def test_round_trip_preserves_all_defaults(tmp_dir):
    """Writing a default AppConfig and reading it back should preserve all defaults."""
    out_path = os.path.join(tmp_dir, "roundtrip.ini")
    cfg1 = AppConfig()
    cfg1.to_ini(path=out_path)
    cfg2 = AppConfig.from_ini(path=out_path)

    # Check every field
    assert cfg1 == cfg2


def test_from_ini_missing_file_uses_defaults(tmp_dir):
    """If config file doesn't exist, from_ini should return defaults."""
    nonexistent = os.path.join(tmp_dir, "no_such_file.ini")
    cfg = AppConfig.from_ini(path=nonexistent)
    assert cfg.main_mode == 1
    assert cfg.website == "all"


def test_from_ini_missing_section_uses_defaults(tmp_dir):
    """If a section is missing, from_ini should use defaults for those fields."""
    # Write a minimal config missing several sections
    minimal = os.path.join(tmp_dir, "minimal.ini")
    with open(minimal, "w", encoding="utf-8") as f:
        f.write("[common]\nmain_mode = 2\n")

    cfg = AppConfig.from_ini(path=minimal)
    assert cfg.main_mode == 2
    assert cfg.website == "all"  # default
    assert cfg.proxy_type == "no"  # default from missing section


def test_get_proxies_dict_no_proxy():
    """get_proxies_dict should return empty dict when proxy_type is 'no'."""
    cfg = AppConfig(proxy_type="no", proxy="")
    assert cfg.get_proxies_dict() == {}


def test_get_proxies_dict_http():
    """get_proxies_dict should return http proxy dict."""
    cfg = AppConfig(proxy_type="http", proxy="127.0.0.1:7890")
    assert cfg.get_proxies_dict() == {"http": "http://127.0.0.1:7890"}


def test_get_proxies_dict_socks5():
    """get_proxies_dict should return socks5 proxy dict."""
    cfg = AppConfig(proxy_type="socks5", proxy="127.0.0.1:1080")
    assert cfg.get_proxies_dict() == {"socks5": "socks5://127.0.0.1:1080"}
