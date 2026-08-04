"""Shared fixtures for scraper tests."""
from pathlib import Path

import pytest


FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures" / "html"


@pytest.fixture
def load_fixture():
    """Load an HTML fixture file by name."""
    def _load(name: str) -> str:
        path = FIXTURES_DIR / name
        return path.read_text(encoding="utf-8")
    return _load
