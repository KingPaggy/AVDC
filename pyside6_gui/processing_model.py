"""ProcessingModel — QML 可访问的 CoreEngine 包装器。

将 core 层的 CoreEngine 包装为 QObject，通过 Qt Signal/Slot 暴露给 QML。
"""
from PySide6.QtCore import QObject, Signal, Slot, Property


class ProcessingModel(QObject):
    """QML 可访问的处理模型。

    Signals:
        isProcessingChanged: 处理状态变化时发射
        logMessage: 日志消息 (level: str, message: str)
        progressChanged: 进度变化 (value: float 0.0-1.0)
        movieProcessed: 单文件处理完成 (number: str, success: bool)
        batchProgress: 批量进度 (current: int, total: int)
        processingFinished: 批量处理完成 (success_count: int, fail_count: int, skip_count: int)
    """

    # --- 状态信号 ---
    isProcessingChanged = Signal(bool)

    # --- 进度信号 ---
    progressChanged = Signal(float)       # 0.0 - 1.0
    batchProgress = Signal(int, int)      # current, total
    processingFinished = Signal(int, int, int)  # success, fail, skip

    # --- 事件信号 ---
    logMessage = Signal(str, str)         # level, message
    movieProcessed = Signal(str, bool)    # number, success

    def __init__(self, config_model=None, parent=None):
        super().__init__(parent)
        self._is_processing = False
        self._config_model = config_model
        self._stop_requested = False

    # --- 属性 ---
    @Property(bool, notify=isProcessingChanged)
    def isProcessing(self):
        return self._is_processing

    @isProcessing.setter
    def isProcessing(self, value: bool):
        if self._is_processing != value:
            self._is_processing = value
            self.isProcessingChanged.emit(value)

    # --- Slot ---
    @Slot()
    def stop(self):
        """请求停止当前处理。"""
        self._stop_requested = True

    def _reset_stop_flag(self):
        self._stop_requested = False

    def _emit_log(self, level: str, message: str):
        """内部日志发射辅助。"""
        self.logMessage.emit(level, message)

    def _emit_progress(self, value: float):
        """内部进度发射辅助。"""
        self.progressChanged.emit(value)
