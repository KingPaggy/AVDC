from abc import ABC, abstractmethod
from typing import Optional
from core.models import Movie


class ScraperBase(ABC):
    """Base class for all scrapers. Defines the interface contract."""

    name: str = ""
    priority: int = 100

    @abstractmethod
    def scrape(
        self, number: str, appoint_url: str = "", is_uncensored: bool = False
    ) -> Movie:
        """
        Scrape metadata for a given video number.

        Args:
            number: The video number/catalog ID
            appoint_url: Optional pre-determined URL to scrape from
            is_uncensored: Whether this is an uncensored video

        Returns:
            Movie object with scraped data
        """
        pass

    def is_timeout(self, movie: Movie) -> bool:
        return movie.website == "timeout"

    def is_empty(self, movie: Movie) -> bool:
        return not movie.is_valid()

    def scrape_with_fallback(
        self, number: str, appoint_url: str = "", is_uncensored: bool = False
    ) -> Movie:
        """Wrapper that handles exceptions and returns empty movie on failure."""
        try:
            return self.scrape(number, appoint_url, is_uncensored)
        except Exception as e:
            print(f"Error in {self.name}.scrape: {e}")
            return Movie.empty()


class ScraperRegistry:
    """Registry for managing scraper instances and dispatch."""

    _scrapers: list[ScraperBase] = []

    @classmethod
    def register(cls, scraper: ScraperBase) -> None:
        cls._scrapers.append(scraper)

    @classmethod
    def get_scrapers(cls) -> list[ScraperBase]:
        return sorted(cls._scrapers, key=lambda s: s.priority)

    @classmethod
    def get_by_name(cls, name: str) -> Optional[ScraperBase]:
        for scraper in cls._scrapers:
            if scraper.name.lower() == name.lower():
                return scraper
        return None

    @classmethod
    def clear(cls) -> None:
        cls._scrapers.clear()


def register_scraper(scraper_class: type[ScraperBase]) -> type[ScraperBase]:
    """Decorator to register a scraper class."""
    ScraperRegistry.register(scraper_class())
    return scraper_class
