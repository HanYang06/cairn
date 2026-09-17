# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""布局原语：只处理几何，不认识内容。

底层就这几个正交原语；复杂的、异形的、非对称的结构靠**嵌套 + 权重/伸缩 + 跨行列**
组合出来，而不是新增原语。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import ClassVar

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
    QGridLayout,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .base import Component


class Box(Component):
    """纵 / 横布局基类；`add` 逐个加子件，支持伸缩与对齐。"""

    _direction: ClassVar[QBoxLayout.Direction] = QBoxLayout.Direction.TopToBottom

    def __init__(
        self,
        *children: QWidget,
        spacing: int = 0,
        margins: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._box = QBoxLayout(self._direction, self)
        self._box.setSpacing(spacing)
        self._box.setContentsMargins(margins, margins, margins, margins)
        for child in children:
            self.add(child)

    def add(
        self,
        child: QWidget,
        *,
        stretch: int = 0,
        alignment: Qt.AlignmentFlag | None = None,
    ) -> QWidget:
        """把一个子件加进布局；返回该子件便于链式使用。"""
        if alignment is None:
            self._box.addWidget(child, stretch)
        else:
            self._box.addWidget(child, stretch, alignment)
        return child


class VBox(Box):
    """纵向布局。"""

    _direction: ClassVar[QBoxLayout.Direction] = QBoxLayout.Direction.TopToBottom


class HBox(Box):
    """横向布局。"""

    _direction: ClassVar[QBoxLayout.Direction] = QBoxLayout.Direction.LeftToRight


class Grid(Component):
    """网格布局：按 (行, 列) 放置，可跨行列。"""

    def __init__(
        self,
        *,
        spacing: int = 0,
        margins: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._grid = QGridLayout(self)
        self._grid.setSpacing(spacing)
        self._grid.setContentsMargins(margins, margins, margins, margins)

    def add(  # noqa: PLR0913 — 网格定位参数本就需要行列跨距
        self,
        child: QWidget,
        row: int,
        column: int,
        *,
        row_span: int = 1,
        column_span: int = 1,
        alignment: Qt.AlignmentFlag | None = None,
    ) -> QWidget:
        """把子件放到 (row, column)，可跨 `row_span` / `column_span`。"""
        if alignment is None:
            self._grid.addWidget(child, row, column, row_span, column_span)
        else:
            self._grid.addWidget(child, row, column, row_span, column_span, alignment)
        return child


class Split(Component):
    """可拖拽分隔：包一层 `QSplitter`，方向横 / 纵。"""

    def __init__(
        self,
        *children: QWidget,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._splitter = QSplitter(orientation, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._splitter)
        for child in children:
            self.add(child)

    @property
    def splitter(self) -> QSplitter:
        """底层 `QSplitter`（设置伸缩 / 初始尺寸时用）。"""
        return self._splitter

    def add(self, child: QWidget, *, stretch: int = 0) -> QWidget:
        """加一个可拖拽子件；`stretch` 控制拖动时的伸缩权。"""
        index = self._splitter.count()
        self._splitter.addWidget(child)
        if stretch:
            self._splitter.setStretchFactor(index, stretch)
        return child


__all__ = ["Box", "Grid", "HBox", "Split", "VBox"]
