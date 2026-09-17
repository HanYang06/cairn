# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""格式工具栏：按内核注册表的预设布局渲染两行工具，点击发 ``tool_triggered(id, source)``。

布局 / 图标 / 标题都来自 `domains.note.tools`（`PRESET_LAYOUT` + `tool_info()`），
界面只负责呈现与转发意图。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Signal

from ...domains.note.tools import PRESET_LAYOUT, tool_info
from ..layout import HBox, VBox
from .atoms import Button, Divider, IconButton

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


class FormatToolbar(VBox):
    """两行格式工具条；行为由上层（编辑器）执行。"""

    tool_triggered = Signal(str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=2)
        info = {item["id"]: item for item in tool_info()}
        for row in PRESET_LAYOUT:
            row_box = HBox(spacing=2)
            for group in row:
                for tool_id in group:
                    meta = info.get(tool_id)
                    if meta is None or not meta.get("available"):
                        continue
                    row_box.add(self._make_button(tool_id, meta))
                row_box.add(Divider(vertical=True))
            self.add(row_box)

    def _make_button(self, tool_id: str, meta: dict[str, Any]) -> Any:
        tip = str(meta.get("label") or tool_id)
        glyph = str(meta.get("glyph") or "")
        if glyph:
            button: Any = IconButton(glyph, tip=tip)
        else:
            button = Button(str(meta.get("text") or ""), role="ToolButton")
            button.control.setToolTip(tip)
        button.clicked.connect(lambda: self.tool_triggered.emit(tool_id, button))
        return button


__all__ = ["FormatToolbar"]
