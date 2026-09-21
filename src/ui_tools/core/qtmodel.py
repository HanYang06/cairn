# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt 模型桥：把类型化 `Model[T]` 适配成 `QAbstractItemModel`。

`Model` 变更即整表 reset（不造细粒度 diff / reconciler）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .model import Model

_NO_INDEX = QModelIndex()


class QtListModel(QAbstractListModel):
    """`Model[T]` → `QAbstractListModel`（行文本由 `row` 决定）。"""

    def __init__(
        self,
        model: Model[Any],
        row: Callable[[Any], str],
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._row = row
        self._cancel = model.watch(self._reset)
        # C++ 对象被销毁时自动退订，避免回调打到已删除的 QObject。
        self.destroyed.connect(self._on_destroyed)

    def _on_destroyed(self, _obj: object = None) -> None:
        self.detach()

    def _reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def rowCount(  # noqa: N802 — Qt 覆写
        self,
        parent: QModelIndex | QPersistentModelIndex = _NO_INDEX,
    ) -> int:
        del parent
        return len(self._model)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        return self._row(self._model.items()[index.row()])

    def detach(self) -> None:
        """断开对 `Model` 的观察。"""
        self._cancel()


__all__ = ["QtListModel"]
