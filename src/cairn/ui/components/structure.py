# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""结构件：语义化组合（工具条 / 分区 / 列表面板…）。

结构件本身就是组合类型，可以再组合，深度不设限；只负责组织与联动，不写业务。
联动通过共享状态 / 控制器产生，不靠控件之间直接连线。见 `rules/references/ui-boundary.md` §6。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal

from .atoms import IconButton
from .layout import HBox

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class Toolbar(HBox):
    """工具条：一组图标按钮；点击发 ``triggered(action_id)`` 意图。"""

    triggered = Signal(str)

    def __init__(self, *, spacing: int = 4, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=spacing)

    def add_action(self, action_id: str, glyph: str, *, tip: str = "") -> IconButton:
        """加一个图标动作；点击时发 ``triggered(action_id)``。"""
        button = IconButton(glyph, tip=tip, on_click=lambda: self.triggered.emit(action_id))
        self.add(button)
        return button


__all__ = ["Toolbar"]
