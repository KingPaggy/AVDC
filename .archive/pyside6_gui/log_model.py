"""
LogModel — 高性能日志模型，支持级别过滤和数量限制。

在 Python 侧管理日志数据，只将符合条件的日志传递给 QML，
避免 QML delegate.visible 的内存开销。

Features:
- 级别过滤 (all/error/warn/info/debug)
- 最大条数限制，自动删除最旧日志
- Qt Model 虚拟化，QML 只渲染可见行
- O(1) 添加，O(n) 批量删除
"""

from typing import Optional
from datetime import datetime
from PySide6.QtCore import (
    QObject, Signal, Slot, Property,
    QAbstractListModel, QModelIndex, Qt
)


class LogEntry:
    """单条日志数据。"""
    __slots__ = ['level', 'message', 'timestamp']

    def __init__(self, level: str, message: str, timestamp: str):
        self.level = level
        self.message = message
        self.timestamp = timestamp


class LogListModel(QAbstractListModel):
    """Qt AbstractListModel for QML ListView — 高性能虚拟化。

    QML ListView 只会为可见行请求 data()，而非全部数据。
    这实现了真正的虚拟化：1000 条日志可能只渲染 20 个 delegate。

    Roles:
        - LevelRole: 日志级别 (ERROR/WARN/INFO/DEBUG)
        - MessageRole: 日志内容
        - TimestampRole: 时间戳
    """

    # Model roles
    LevelRole = Qt.ItemDataRole.UserRole + 1
    MessageRole = Qt.ItemDataRole.UserRole + 2
    TimestampRole = Qt.ItemDataRole.UserRole + 3

    # Signals
    countChanged = Signal(int)

    def __init__(self, max_entries: int = 1000, parent=None):
        super().__init__(parent)
        self._entries: list[LogEntry] = []
        self._max_entries = max_entries

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._entries) if not parent.isValid() else 0

    def data(self, index: QModelIndex, role: int) -> Optional[str]:
        if not index.isValid() or index.row() >= len(self._entries):
            return None
        entry = self._entries[index.row()]
        if role == self.LevelRole:
            return entry.level
        elif role == self.MessageRole:
            return entry.message
        elif role == self.TimestampRole:
            return entry.timestamp
        return None

    def roleNames(self) -> dict[int, str]:
        return {
            self.LevelRole: 'level',
            self.MessageRole: 'message',
            self.TimestampRole: 'timestamp',
        }

    def append(self, entry: LogEntry) -> None:
        """添加日志条目。"""
        row = len(self._entries)
        self.beginInsertRows(QModelIndex(), row, row)
        self._entries.append(entry)
        self.endInsertRows()

        # 超出限制时批量删除最旧的日志
        excess = len(self._entries) - self._max_entries
        if excess > 0:
            self.beginRemoveRows(QModelIndex(), 0, excess - 1)
            self._entries = self._entries[excess:]
            self.endRemoveRows()

        self.countChanged.emit(len(self._entries))

    def clear(self) -> None:
        """清空所有日志。"""
        if not self._entries:
            return
        self.beginRemoveRows(QModelIndex(), 0, len(self._entries) - 1)
        self._entries.clear()
        self.endRemoveRows()
        self.countChanged.emit(0)

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._entries)


class LogFilterModel(QObject):
    """日志过滤模型 — 管理级别过滤和数据转发。

    暴露给 QML 的接口：
    - filterLevel: 过滤级别 (all/error/warn/info/debug)
    - filteredModel: 过滤后的 QAbstractListModel
    - totalCount: 未过滤的总日志数
    - addEntry(level, message): 添加日志
    - clearAll(): 清空日志
    """

    # 级别映射：统一日志级别名称
    LEVEL_MAP = {
        'ERROR': 'ERROR',
        'ERR': 'ERROR',
        'WARN': 'WARN',
        'WARNING': 'WARN',
        'INFO': 'INFO',
        'DEBUG': 'DEBUG',
        'SEPARATOR': 'INFO',  # 分隔线当作 INFO
    }

    # 级别优先级（用于过滤）
    LEVEL_PRIORITY = {
        'ERROR': 0,
        'WARN': 1,
        'INFO': 2,
        'DEBUG': 3,
    }

    # Signals
    filterLevelChanged = Signal(str)
    countChanged = Signal(int)

    def __init__(self, max_entries: int = 1000, parent=None):
        super().__init__(parent)
        self._filter_level = 'all'  # all/error/warn/info/debug
        self._source_model = LogListModel(max_entries=max_entries, parent=self)
        self._filtered_model = LogListModel(max_entries=max_entries, parent=self)

    # ===== Properties =====

    @Property(str, notify=filterLevelChanged)
    def filterLevel(self) -> str:
        return self._filter_level

    @filterLevel.setter
    def filterLevel(self, value: str):
        if self._filter_level != value:
            self._filter_level = value
            self._rebuild_filtered_model()
            self.filterLevelChanged.emit(value)

    @Property(QObject, constant=True)
    def filteredModel(self) -> LogListModel:
        """QML ListView 绑定的模型。"""
        return self._filtered_model

    @Property(int, notify=countChanged)
    def totalCount(self) -> int:
        """未过滤的总日志数。"""
        return self._source_model.count

    # ===== Slots =====

    @Slot(str, str)
    def addEntry(self, level: str, message: str) -> None:
        """添加日志（从 LogBridge 调用）。"""
        if not message:
            return

        # 统一级别名称
        normalized = self.LEVEL_MAP.get(level.upper(), 'INFO')

        # 生成时间戳
        timestamp = datetime.now().strftime('%H:%M:%S')

        entry = LogEntry(normalized, message, timestamp)

        # 添加到源模型
        self._source_model.append(entry)

        # 如果符合过滤条件，添加到过滤模型
        if self._matches_filter(normalized):
            self._filtered_model.append(entry)

        self.countChanged.emit(self._source_model.count)

    @Slot()
    def clearAll(self) -> None:
        """清空日志。"""
        self._source_model.clear()
        self._filtered_model.clear()
        self.countChanged.emit(0)

    # ===== Internal =====

    def _matches_filter(self, level: str) -> bool:
        """检查级别是否匹配当前过滤条件。"""
        if self._filter_level == 'all':
            return True

        # 过滤级别到显示级别的映射
        # error: 只显示 ERROR
        # warn: 显示 ERROR + WARN
        # info: 显示 ERROR + WARN + INFO
        # debug: 显示全部
        filter_priority = {
            'error': 0,
            'warn': 1,
            'info': 2,
            'debug': 3,
        }

        threshold = filter_priority.get(self._filter_level, 2)
        level_priority = self.LEVEL_PRIORITY.get(level, 2)

        return level_priority <= threshold

    def _rebuild_filtered_model(self) -> None:
        """根据过滤条件重建过滤模型。"""
        self._filtered_model.clear()

        for entry in self._source_model._entries:
            if self._matches_filter(entry.level):
                self._filtered_model._entries.append(entry)

        # 通知 QML 数据变化
        if self._filtered_model._entries:
            # 使用 beginResetModel/endResetModel 批量更新
            self._filtered_model.beginResetModel()
            self._filtered_model.endResetModel()
            self._filtered_model.countChanged.emit(len(self._filtered_model._entries))