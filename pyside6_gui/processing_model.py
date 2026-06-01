"""ProcessingModel — QML 可访问的 CoreEngine 包装器。

将 core 层的 CoreEngine 包装为 QObject，通过 Qt Signal/Slot 暴露给 QML。
在后台线程中运行批处理，不阻塞 UI。
"""
import threading
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot, Property, QMutex, QMutexLocker


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

    # --- QML 绑定属性 ---
    progressValueChanged = Signal(float)
    statusTextChanged = Signal(str)
    successCountChanged = Signal(int)
    failCountChanged = Signal(int)
    skipCountChanged = Signal(int)

    def __init__(self, config_model=None, parent=None):
        super().__init__(parent)
        self._is_processing = False
        self._config_model = config_model
        self._stop_requested = False
        self._worker_thread: Optional[threading.Thread] = None
        self._mutex = QMutex()

        # QML 绑定属性内部状态
        self._progress_value = 0.0
        self._status_text = "就绪"
        self._success_count = 0
        self._fail_count = 0
        self._skip_count = 0

    # --- 属性 ---
    @Property(bool, notify=isProcessingChanged)
    def isProcessing(self):
        return self._is_processing

    @isProcessing.setter
    def isProcessing(self, value: bool):
        if self._is_processing != value:
            self._is_processing = value
            self.isProcessingChanged.emit(value)

    @Property(float, notify=progressValueChanged)
    def progressValue(self):
        return self._progress_value

    @Property(str, notify=statusTextChanged)
    def statusText(self):
        return self._status_text

    @Property(int, notify=successCountChanged)
    def successCount(self):
        return self._success_count

    @Property(int, notify=failCountChanged)
    def failCount(self):
        return self._fail_count

    @Property(int, notify=skipCountChanged)
    def skipCount(self):
        return self._skip_count

    # --- 公共 Slot ---
    @Slot()
    def stop(self):
        """请求停止当前处理。"""
        with QMutexLocker(self._mutex):
            self._stop_requested = True

    def _reset_stop_flag(self):
        with QMutexLocker(self._mutex):
            self._stop_requested = False

    @property
    def _should_stop(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._stop_requested

    @Slot(str, str, int)
    def start_batch(self, movie_path: str, escape_folder: str = "", scraper_mode: int = 1):
        """开始批量处理。

        Args:
            movie_path: 视频文件目录
            escape_folder: 排除文件夹（逗号分隔）
            scraper_mode: 1=all, 2=mgstage, 3=javbus, 4=jav321, 5=javdb/fc2, 6=avsox, 7=xcity, 8=dmm
        """
        if self._is_processing:
            self._emit_log("WARN", "已在处理中，请先停止")
            return

        if not self._config_model:
            self._emit_log("ERROR", "配置模型未初始化")
            return

        self.isProcessing = True
        self._reset_stop_flag()
        self._update_counts(0, 0, 0)
        self._emit_progress(0.0)
        self._emit_log("INFO", f"开始批量处理: {movie_path}")

        # 创建回调（在 worker 线程中调用）
        def on_log(msg: str):
            self.logMessage.emit("INFO", msg)

        def on_progress(current: int, total: int, filepath: str):
            self.batchProgress.emit(current, total)
            value = current / total if total > 0 else 0.0
            self._emit_progress(value)
            import os
            self._emit_log("INFO", f"[{current}/{total}] {os.path.basename(filepath)}")

        def on_success(filepath: str, suffix: str):
            from core._files.file_utils import getNumber
            number = getNumber(filepath, "") or filepath
            self.movieProcessed.emit(number, True)

        def on_failure(filepath: str, reason: str, error: Exception):
            from core._files.file_utils import getNumber
            number = getNumber(filepath, "") or filepath
            self.movieProcessed.emit(number, False)
            self._emit_log("ERROR", f"失败: {filepath} ({reason})")

        # 在后台线程运行
        def _worker():
            try:
                from core._config.config import AppConfig
                from core._services.orchestrator import CoreEngine

                cfg = self._config_model.to_app_config()
                engine = CoreEngine(
                    config=cfg,
                    on_log=on_log,
                    on_progress=on_progress,
                    on_success=on_success,
                    on_failure=on_failure,
                )

                result = engine.process_batch(
                    movie_path=movie_path,
                    escape_folder=escape_folder,
                    scraper_mode=scraper_mode,
                )

                total = result.get("total", 0)
                success = result.get("success", 0)
                failed = result.get("failed", 0)
                skipped = total - success - failed
                self._update_counts(success, failed, skipped)
                self.processingFinished.emit(success, failed, skipped)
                self._emit_log("INFO", f"完成: {total} 个文件, 成功 {success}, 失败 {failed}")

            except Exception as exc:
                self._emit_log("ERROR", f"处理异常: {exc}")
                self.processingFinished.emit(0, 0, 0)
            finally:
                # 回到主线程设置状态
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, "_finishProcessing", Qt.QueuedConnection)

        self._worker_thread = threading.Thread(target=_worker, daemon=True)
        self._worker_thread.start()

    @Slot()
    def start_single(self, filepath: str, number: str, scraper_mode: int = 1, appoint_url: str = ""):
        """处理单个文件。"""
        if self._is_processing:
            self._emit_log("WARN", "已在处理中，请先停止")
            return

        if not self._config_model:
            self._emit_log("ERROR", "配置模型未初始化")
            return

        self.isProcessing = True
        self._reset_stop_flag()

        def on_log(msg: str):
            self.logMessage.emit("INFO", msg)

        def on_success(f: str, suffix: str):
            self.movieProcessed.emit(number, True)

        def on_failure(f: str, reason: str, error: Exception):
            self.movieProcessed.emit(number, False)
            self._emit_log("ERROR", f"失败: {reason}")

        def _worker():
            try:
                from core._config.config import AppConfig
                from core._services.orchestrator import CoreEngine

                cfg = self._config_model.to_app_config()
                engine = CoreEngine(
                    config=cfg,
                    on_log=on_log,
                    on_success=on_success,
                    on_failure=on_failure,
                )

                engine.process_single(
                    filepath=filepath,
                    number=number,
                    scraper_mode=scraper_mode,
                    appoint_url=appoint_url,
                )

                self.processingFinished.emit(1, 0, 0)

            except Exception as exc:
                self._emit_log("ERROR", f"处理异常: {exc}")
                self.processingFinished.emit(0, 1, 0)
            finally:
                from PySide6.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, "_finishProcessing", Qt.QueuedConnection)

        self._worker_thread = threading.Thread(target=_worker, daemon=True)
        self._worker_thread.start()

    @Slot()
    def _finishProcessing(self):
        """内部方法 — 工作线程完成后恢复状态（必须在主线程调用）。"""
        self._reset_stop_flag()
        self._emit_progress(1.0)
        self.isProcessing = False

    # --- 内部辅助 ---
    def _emit_log(self, level: str, message: str):
        """内部日志发射辅助。"""
        self.logMessage.emit(level, message)
        # 更新状态文字
        self._status_text = message
        self.statusTextChanged.emit(message)

    def _emit_progress(self, value: float):
        """内部进度发射辅助。"""
        self._progress_value = value
        self.progressValueChanged.emit(value)
        self.progressChanged.emit(value)

    def _update_counts(self, success: int, fail: int, skip: int):
        """更新计数属性。"""
        self._success_count = success
        self._fail_count = fail
        self._skip_count = skip
        self.successCountChanged.emit(success)
        self.failCountChanged.emit(fail)
        self.skipCountChanged.emit(skip)
