"""Abstract settings provider for core services.

Core services query this interface for runtime configuration instead of
reaching into UI widgets directly.
"""

from abc import ABC, abstractmethod


class SettingsProvider(ABC):
    """Abstract interface for querying runtime settings."""

    # --- Debug ---
    @abstractmethod
    def is_debug_enabled(self) -> bool: ...

    # --- Run mode ---
    @abstractmethod
    def is_program_mode_move(self) -> bool: ...

    # --- Download control ---
    @abstractmethod
    def should_download_thumb(self) -> bool: ...
    @abstractmethod
    def should_download_poster(self) -> bool: ...
    @abstractmethod
    def should_download_fanart(self) -> bool: ...
    @abstractmethod
    def should_download_nfo(self) -> bool: ...

    # --- Image processing ---
    @abstractmethod
    def should_copy_fanart(self) -> bool: ...
    @abstractmethod
    def should_restore_imagecut(self) -> bool: ...

    # --- Extra features ---
    @abstractmethod
    def is_extrafanart_enabled(self) -> bool: ...
    @abstractmethod
    def is_print_enabled(self) -> bool: ...

    # --- Watermark config ---
    @abstractmethod
    def get_mark_config(self) -> dict: ...
