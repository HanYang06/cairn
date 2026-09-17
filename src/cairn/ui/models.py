# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""通用 Qt 模型：把一串类型化行按「字段名 → 取值函数」映射成 Qt role。

目的是消灭每个列表都重写 `QAbstractListModel` 的样板：字段声明一次，列表/树共用。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from PySide6.QtCore import QAbstractItemModel, QAbstractListModel, QModelIndex, QObject, Qt

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


class ListModel[T](QAbstractListModel):
    """类型化行列表模型；字段名即 QML/委托可用的 role 名。"""

    def __init__(
        self,
        fields: Sequence[tuple[str, Callable[[T], object]]],
        *,
        display: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._fields: list[tuple[str, Callable[[T], object]]] = list(fields)
        self._getters: dict[int, Callable[[T], object]] = {
            int(Qt.ItemDataRole.UserRole) + 1 + index: getter
            for index, (_, getter) in enumerate(self._fields)
        }
        self._names: dict[int, bytes] = {
            int(Qt.ItemDataRole.UserRole) + 1 + index: name.encode()
            for index, (name, _) in enumerate(self._fields)
        }
        self._display = display
        self._rows: list[T] = []

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        names = dict(self._names)
        if self._display:
            names[int(Qt.ItemDataRole.DisplayRole)] = self._display.encode()
        return names

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 0 if parent.isValid() else len(self._rows)

    def data(  # type: ignore[override]
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        row = self._rows[index.row()]
        if self._display and role == int(Qt.ItemDataRole.DisplayRole):
            return self._getter(self._display)(row)
        getter = self._getters.get(role)
        return None if getter is None else getter(row)

    def set_rows(self, rows: Sequence[T]) -> None:
        """整体替换行；先重置模型（增量更新后续再加）。"""
        self.beginResetModel()
        self._rows = list(rows)
        self.endResetModel()

    def row_at(self, row: int) -> T | None:
        """按下标取原始行（供意图处理用）。"""
        return self._rows[row] if 0 <= row < len(self._rows) else None

    def _getter(self, name: str) -> Callable[[T], object]:
        for field_name, getter in self._fields:
            if field_name == name:
                return getter
        msg = f"未知字段: {name}"
        raise KeyError(msg)


class _Item:
    """树模型的内部节点包装（持值 / 父 / 子）。"""

    __slots__ = ("children", "parent", "value")

    def __init__(self, value: Any, parent: _Item | None) -> None:
        self.value = value
        self.parent = parent
        self.children: list[_Item] = []

    @property
    def row(self) -> int:
        if self.parent is None:
            return 0
        return self.parent.children.index(self)


class TreeModel[T](QAbstractItemModel):
    """通用树模型：节点按 `children_of` 展开；字段名即 role。"""

    def __init__(
        self,
        fields: Sequence[tuple[str, Callable[[T], object]]],
        children_of: Callable[[T], Sequence[T]],
        *,
        display: str = "",
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._fields: list[tuple[str, Callable[[T], object]]] = list(fields)
        self._children_of = children_of
        self._getters: dict[int, Callable[[T], object]] = {
            int(Qt.ItemDataRole.UserRole) + 1 + index: getter
            for index, (_, getter) in enumerate(self._fields)
        }
        self._names: dict[int, bytes] = {
            int(Qt.ItemDataRole.UserRole) + 1 + index: name.encode()
            for index, (name, _) in enumerate(self._fields)
        }
        self._display = display
        self._roots: list[_Item] = []

    def roleNames(self) -> dict[int, bytes]:  # type: ignore[override]
        names = dict(self._names)
        if self._display:
            names[int(Qt.ItemDataRole.DisplayRole)] = self._display.encode()
        return names

    def columnCount(self, _parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        return 1

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # type: ignore[override]
        if not parent.isValid():
            return len(self._roots)
        item: _Item = parent.internalPointer()
        return len(item.children)

    def index(  # type: ignore[override]
        self,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if parent.isValid():
            parent_item: _Item = parent.internalPointer()
            child = parent_item.children[row]
        else:
            child = self._roots[row]
        return self.createIndex(row, column, child)

    def parent(self, index: QModelIndex) -> QModelIndex:  # type: ignore[override]
        if not index.isValid():
            return QModelIndex()
        item: _Item = index.internalPointer()
        above = item.parent
        if above is None:
            return QModelIndex()
        return self.createIndex(above.row, 0, above)

    def data(  # type: ignore[override]
        self,
        index: QModelIndex,
        role: int = int(Qt.ItemDataRole.DisplayRole),
    ) -> Any:
        if not index.isValid():
            return None
        item: _Item = index.internalPointer()
        if self._display and role == int(Qt.ItemDataRole.DisplayRole):
            return self._getter(self._display)(item.value)
        getter = self._getters.get(role)
        return None if getter is None else getter(item.value)

    def set_roots(self, roots: Sequence[T]) -> None:
        """整体替换根节点（先重置模型）。"""
        self.beginResetModel()
        self._roots = [self._make(value, None) for value in roots]
        self.endResetModel()

    def value_at(self, index: QModelIndex) -> T | None:
        """取索引处的原始节点。"""
        if not index.isValid():
            return None
        item: _Item = index.internalPointer()
        return cast("T", item.value)

    def _make(self, value: T, parent: _Item | None) -> _Item:
        item = _Item(value, parent)
        item.children = [self._make(child, item) for child in self._children_of(value)]
        return item

    def _getter(self, name: str) -> Callable[[T], object]:
        for field_name, getter in self._fields:
            if field_name == name:
                return getter
        msg = f"未知字段: {name}"
        raise KeyError(msg)


__all__ = ["ListModel", "TreeModel"]
