# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""布局原语测试：组合与几何。"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSplitter

from cairn.ui.layout import Grid, HBox, Split, Stack, VBox

pytestmark = pytest.mark.usefixtures("qapp")


def _label(text: str) -> QLabel:
    return QLabel(text)


def test_vbox_holds_children_in_order() -> None:
    box = VBox(_label("a"), _label("b"))
    box.add(_label("c"))
    assert box.layout() is not None
    assert box.layout().count() == 3


def test_hbox_matches_box() -> None:
    box = HBox(spacing=4, margins=2)
    box.add(_label("x"), stretch=1)
    layout = box.layout()
    assert layout is not None
    assert layout.count() == 1


def test_grid_places_by_row_column() -> None:
    grid = Grid(spacing=2)
    grid.add(_label("a"), 0, 0, column_span=2)
    grid.add(_label("b"), 1, 0)
    grid.add(_label("c"), 1, 1)
    layout = grid.layout()
    assert layout is not None
    assert layout.count() == 3


def test_split_drags_between_panes() -> None:
    split = Split(
        _label("nav"),
        _label("main"),
        _label("insp"),
        orientation=Qt.Orientation.Horizontal,
    )
    split.splitter.setStretchFactor(1, 1)
    assert isinstance(split.splitter, QSplitter)
    assert split.splitter.count() == 3


def test_stack_switches_children() -> None:
    stack = Stack(_label("a"), _label("b"))
    assert stack.stack.count() == 2
    stack.set_current(1)
    assert stack.stack.currentIndex() == 1
