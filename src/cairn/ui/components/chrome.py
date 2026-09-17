# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""标题栏 / 状态栏：窗口上下的信息条（结构件）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..layout import HBox
from .atoms import Label

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class TitleBar(HBox):
    """窗口顶部标题条：显示应用 / 当前上下文。"""

    def __init__(self, title: str = "Cairn", parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=8, margins=8)
        self._label = Label(title)
        self.add(self._label, stretch=1)

    def set_text(self, text: str) -> None:
        """更新标题文字。"""
        self._label.text = text


class StatusBar(HBox):
    """窗口底部状态条。"""

    def __init__(self, message: str = "就绪", parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=8, margins=6)
        self._label = Label(message, role="Faint")
        self.add(self._label, stretch=1)

    def set_message(self, text: str) -> None:
        """更新状态文字。"""
        self._label.text = text


__all__ = ["StatusBar", "TitleBar"]
