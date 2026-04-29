"""Thread-safe event bus for publish/subscribe communication."""

import threading
from typing import Callable

from core._event.events import Event, EventType


class EventBus:
    """Thread-safe event pub/sub bus.

    Usage:
        bus = EventBus()
        bus.on(EventType.LOG_INFO, lambda e: print(e.message))
        bus.emit(EventType.LOG_INFO, message="hello")
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()

    def on(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Register an event handler."""
        with self._lock:
            self._handlers.setdefault(event_type, []).append(handler)

    def off(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Unregister an event handler."""
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]

    def emit(self, event_type: EventType, **kwargs) -> None:
        """Emit an event to all registered handlers. Thread-safe."""
        import time

        event = Event(type=event_type, data=kwargs)
        with self._lock:
            handlers = list(self._handlers.get(event_type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Don't let one handler break the chain
                pass

    def clear(self) -> None:
        """Remove all handlers."""
        with self._lock:
            self._handlers.clear()
