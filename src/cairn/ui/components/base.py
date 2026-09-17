# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组件基类与容器：`Component`（见 `ui/component.py`）+ `Panel`（可停靠侧栏）。

`Component` 本体在中性位置 `ui/component.py`；这里放只属于「组件库」的东西。
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..component import Component


class Panel(Component):
    """可停靠侧栏内容的容器：标题 + 内容区。"""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = QLabel(title)
        self._title.setObjectName("PanelTitle")
        self._body = QWidget()
        self._body.setObjectName("PanelBody")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._title)
        layout.addWidget(self._body, 1)

    @property
    def body(self) -> QWidget:
        """内容容器；调用方把实际控件加进它的布局。"""
        return self._body

    def set_title(self, text: str) -> None:
        """更新标题栏文字。"""
        self._title.setText(text)


__all__ = ["Component", "Panel"]
