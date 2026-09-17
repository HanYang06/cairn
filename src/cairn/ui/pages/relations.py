# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""关系页：用列表展示当前笔记的上下游（来源 / 派生）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout

from ..components import ListPanel
from .base import Page

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from ..models import ListModel
    from ..rows import RelationRow


class RelationsPage(Page):
    """关系视图页；点行发 ``activated(oid)`` 打开对应笔记。"""

    activated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.panel = ListPanel("关系", key_of=lambda row: row.oid)
        self.panel.activated.connect(self.activated.emit)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.panel)

    def set_model(self, model: ListModel[RelationRow]) -> None:
        """绑定关系模型。"""
        self.panel.set_model(model)


__all__ = ["RelationsPage"]
