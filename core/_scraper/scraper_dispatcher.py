import re
from typing import Optional
from core._models.models import Movie
from core._scraper.scraper_adapter import ScraperAdapter, cache_key, get_cached
from core._config.errors import ScrapingError


class ScraperDispatcher:
    """Handles scraper dispatch logic based on video number patterns."""

    SCRAPER_MAPPING = {
        "javbus": {
            "normal": lambda n, u: ("javbus.main", 10),
            "uncensored": lambda n, u: ("javbus.main_uncensored", 5),
            "us": lambda n, u: ("javbus.main_us", 15),
        },
        "javdb": {
            "normal": lambda n, u: ("javdb.main", 20),
            "uncensored": lambda n, u: ("javdb.main", 25),
            "us": lambda n, u: ("javdb.main_us", 30),
        },
        "jav321": {
            "normal": lambda n, u: ("jav321.main", 40),
            "uncensored": lambda n, u: ("jav321.main", 35),
        },
        "avsox": {
            "normal": lambda n, u: ("avsox.main", 50),
        },
        "mgstage": {
            "normal": lambda n, u: ("mgstage.main", 5),
        },
        "xcity": {
            "normal": lambda n, u: ("xcity.main", 60),
        },
        "dmm": {
            "normal": lambda n, u: ("dmm.main", 70),
        },
    }

    @staticmethod
    def is_uncensored(number: str) -> bool:
        if re.match(r"^\d{4,}", number) or re.match(r"n\d{4}", number):
            return True
        if "HEYZO" in number.upper():
            return True
        return False

    @staticmethod
    def is_fc2(number: str) -> bool:
        return "FC2" in number.upper()

    @staticmethod
    def is_european(number: str) -> bool:
        return bool(re.search(r"\D+\.\d{2}\.\d{2}\.\d{2}", number))

    @staticmethod
    def is_mgstage(number: str) -> bool:
        return bool(re.match(r"\d+[a-zA-Z]+-\d+", number)) or "SIRO" in number.upper()

    @staticmethod
    def is_dmm_style(number: str) -> bool:
        return bool(
            re.match(r"\D{2,}00\d{3,}", number)
            and "-" not in number
            and "_" not in number
        )

    @classmethod
    def get_scraper_chain(cls, number: str, mode: int = 1) -> list[tuple[str, int]]:
        """Get the ordered list of scrapers to try for a given number."""
        if mode == 1:
            return cls._get_auto_chain(number)
        elif mode == 2:
            return [("mgstage.main", 5)]
        elif mode == 3:
            return cls._get_javbus_chain(number)
        elif mode == 4:
            return [("jav321.main", 40)]
        elif mode == 5:
            return cls._get_javdb_chain(number)
        elif mode == 6:
            return [("avsox.main", 50)]
        elif mode == 7:
            return [("xcity.main", 60)]
        elif mode == 8:
            return [("dmm.main", 70)]
        return []

    @classmethod
    def _get_auto_chain(cls, number: str) -> list[tuple[str, int]]:
        if cls.is_uncensored(number):
            return [
                ("javbus.main_uncensored", 5),
                ("javdb.main", 10),
                ("jav321.main", 15),
                ("avsox.main", 20),
            ]
        elif cls.is_fc2(number):
            return [("javdb.main", 10)]
        elif cls.is_mgstage(number):
            return [
                ("mgstage.main", 5),
                ("jav321.main", 10),
                ("javdb.main", 15),
                ("javbus.main", 20),
            ]
        elif cls.is_dmm_style(number):
            return [("dmm.main", 10)]
        elif cls.is_european(number):
            return [
                ("javdb.main_us", 10),
                ("javbus.main_us", 15),
            ]
        else:
            return [
                ("javbus.main", 10),
                ("jav321.main", 20),
                ("xcity.main", 30),
                ("javdb.main", 40),
                ("avsox.main", 50),
            ]

    @classmethod
    def _get_javbus_chain(cls, number: str) -> list[tuple[str, int]]:
        if cls.is_uncensored(number):
            return [("javbus.main_uncensored", 5)]
        elif cls.is_european(number):
            return [("javbus.main_us", 10)]
        return [("javbus.main", 10)]

    @classmethod
    def _get_javdb_chain(cls, number: str) -> list[tuple[str, int]]:
        if cls.is_european(number):
            return [("javdb.main_us", 10)]
        return [("javdb.main", 10)]
