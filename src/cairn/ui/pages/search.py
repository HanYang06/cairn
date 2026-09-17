# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""搜索页：输入即筛，结果列表点选打开笔记。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout

from ..components import Field, ListPanel
from .base import Page

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from ..models import ListModel
    from ..rows import NoteRow


class SearchPage(Page):
    """搜索页：`query_changed` 向上请求过滤，`note_activated` 打开结果。"""

    query_changed = Signal(str)
    note_activated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.field = Field("搜索", placeholder="标题或正文…")
        self.field.edit.textChanged.connect(self.query_changed.emit)
        self.panel = ListPanel("结果", key_of=lambda row: row.oid)
        self.panel.activated.connect(self.note_activated.emit)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 0)
        layout.addWidget(self.field)
        layout.addWidget(self.panel, 1)

    def set_model(self, model: ListModel[NoteRow]) -> None:
        """绑定结果模型。"""
        self.panel.set_model(model)

    def set_query(self, text: str) -> None:
        """填入搜索词（会触发过滤）。"""
        self.field.edit.setText(text)


__all__ = ["SearchPage"]
