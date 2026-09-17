# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""命令面板：搜索并执行命令 / 打开笔记（浮层，`Ctrl+P` 唤起）。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from ..component import Component

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QWidget


class CommandPalette(Component):
    """命令面板浮层；选中项以 ``chosen(kind, key)`` 外发。"""

    chosen = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("CommandPalette")
        self._provider: Callable[[str], list[tuple[str, str, str]]] | None = None
        self._edit = QLineEdit(self)
        self._edit.setPlaceholderText("输入命令或搜索笔记…")
        self._edit.textChanged.connect(self._refresh)
        self._edit.returnPressed.connect(self._activate_current)
        self._list = QListWidget(self)
        self._list.itemActivated.connect(self._activate_item)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._edit)
        layout.addWidget(self._list)
        self.setFixedSize(560, 320)
        self.hide()
        escape = QShortcut(QKeySequence("Escape"), self)
        escape.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        escape.activated.connect(self.close_palette)

    def set_provider(self, provider: Callable[[str], list[tuple[str, str, str]]]) -> None:
        """设置条目提供者：``query -> [(标签, kind, key)]``。"""
        self._provider = provider

    def open_palette(self) -> None:
        """显示面板并聚焦输入。"""
        self._edit.clear()
        self._refresh("")
        parent = self.parentWidget()
        if parent is not None:
            self.move((parent.width() - self.width()) // 2, 72)
        self.show()
        self.raise_()
        self._edit.setFocus()

    def close_palette(self) -> None:
        """隐藏面板。"""
        self.hide()

    def _refresh(self, query: str) -> None:
        self._list.clear()
        items = self._provider(query) if self._provider is not None else []
        for label, kind, key in items:
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, (kind, key))
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)

    def _activate_current(self) -> None:
        item = self._list.currentItem()
        if item is not None:
            self._activate_item(item)

    def _activate_item(self, item: QListWidgetItem) -> None:
        data: Any = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, (tuple, list)) and len(data) == 2:
            self.hide()
            self.chosen.emit(str(data[0]), str(data[1]))


__all__ = ["CommandPalette"]
