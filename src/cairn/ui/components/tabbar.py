# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""标签页结构件：包 `QTabBar`，把打开 / 切换 / 关闭变成意图信号。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTabBar, QVBoxLayout

from ..component import Component

if TYPE_CHECKING:
    from collections.abc import Sequence

    from PySide6.QtWidgets import QWidget

    from ..rows import TabRow


class TabBar(Component):
    """打开标签的横条；激活 / 关闭以意图外发。"""

    activated = Signal(str)
    close_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bar = QTabBar(self)
        self._bar.setObjectName("TabBar")
        self._bar.setExpanding(False)
        self._bar.setTabsClosable(True)
        self._bar.setMovable(False)
        self._bar.currentChanged.connect(self._on_current)
        self._bar.tabCloseRequested.connect(self._on_close)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._bar)
        self._keys: list[str] = []
        self._updating = False

    @property
    def bar(self) -> QTabBar:
        """底层 `QTabBar`。"""
        return self._bar

    def set_tabs(self, tabs: Sequence[TabRow], current_key: str = "") -> None:
        """重建标签；`current_key` 指定当前项。"""
        self._updating = True
        try:
            while self._bar.count():
                self._bar.removeTab(0)
            self._keys = []
            for tab in tabs:
                self._bar.addTab(tab.title)
                self._keys.append(tab.key)
            if current_key in self._keys:
                self._bar.setCurrentIndex(self._keys.index(current_key))
        finally:
            self._updating = False

    def _on_current(self, index: int) -> None:
        if self._updating:
            return
        if 0 <= index < len(self._keys):
            self.activated.emit(self._keys[index])

    def _on_close(self, index: int) -> None:
        if 0 <= index < len(self._keys):
            self.close_requested.emit(self._keys[index])


__all__ = ["TabBar"]
