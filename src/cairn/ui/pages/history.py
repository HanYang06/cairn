# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""历史页：列出版本；双击某版发 ``restore_requested(vid)`` 恢复。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QVBoxLayout

from ..components import ListPanel
from .base import Page

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from ..models import ListModel
    from ..rows import VersionRow


class HistoryPage(Page):
    """版本历史页；双击一行请求恢复到该版本。"""

    restore_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.panel = ListPanel("历史", key_of=lambda row: row.vid)
        self.panel.activated.connect(self.restore_requested.emit)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.panel)

    def set_model(self, model: ListModel[VersionRow]) -> None:
        """绑定历史模型。"""
        self.panel.set_model(model)


__all__ = ["HistoryPage"]
