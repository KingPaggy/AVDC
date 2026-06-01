"""LogBridge — 将 core 层 EventBus 日志转发为 Qt Signal。

订阅 EventBus 的 LOG_INFO / LOG_ERROR / LOG_SEPARATOR 事件，
以 Qt Signal 形式暴露给 QML，实现实时日志流。
"""
from PySide6.QtCore import QObject, Signal


class LogBridge(QObject):
    """EventBus → QML 日志桥接器。

    Signals:
        logReceived(level: str, message: str): 收到日志时发射
            level: "INFO" | "ERROR" | "SEPARATOR"
            message: 日志内容
    """

    logReceived = Signal(str, str)

    def __init__(self, event_bus=None, parent=None):
        super().__init__(parent)
        self._event_bus = event_bus
        self._handlers = {}

    def connect(self):
        """订阅 EventBus 日志事件。"""
        if not self._event_bus:
            return

        from core._event.events import EventType

        self._handlers[EventType.LOG_INFO] = self._on_log_info
        self._handlers[EventType.LOG_ERROR] = self._on_log_error
        self._handlers[EventType.LOG_SEPARATOR] = self._on_log_separator

        for event_type, handler in self._handlers.items():
            self._event_bus.on(event_type, handler)

    def disconnect(self):
        """取消订阅 EventBus 日志事件。"""
        if not self._event_bus:
            return

        for event_type, handler in self._handlers.items():
            self._event_bus.off(event_type, handler)
        self._handlers.clear()

    def _on_log_info(self, event):
        message = getattr(event, "message", "")
        self.logReceived.emit("INFO", message)

    def _on_log_error(self, event):
        message = getattr(event, "message", "")
        self.logReceived.emit("ERROR", message)

    def _on_log_separator(self, event):
        self.logReceived.emit("SEPARATOR", "---")

    def push(self, level: str, message: str):
        """手动推送日志（用于 ProcessingModel 等直接调用）。"""
        self.logReceived.emit(level, message)
