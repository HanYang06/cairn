# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""标签页：列出全部标签；点选发 ``tag_activated(tag)``。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout

from ..components import ListPanel
from .base import Page

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from ..models import ListModel


class TagsPage(Page):
    """标签总览页。"""

    tag_activated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.panel = ListPanel("标签", key_of=lambda tag: tag)
        self.panel.activated.connect(self.tag_activated.emit)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.panel)

    def set_model(self, model: ListModel[str]) -> None:
        """绑定标签模型。"""
        self.panel.set_model(model)


__all__ = ["TagsPage"]
