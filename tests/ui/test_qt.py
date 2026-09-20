# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QWidget

from core import Vault
from core.storage import Block
from ui.component import Component
from ui.core.bridge import Bridge
from ui.core.qt import build
from ui.core.session import Session
from ui.layout import Grid, HBox, VBox
from ui.page import Page

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def test_build_page_with_children() -> None:
    page = Page("root")
    page.set(VBox)
    page.add(Component("a"))
    page.add(Component("b"))

    widget = build(page)

    assert isinstance(widget, QWidget)
    layout = widget.layout()
    assert isinstance(layout, QVBoxLayout)
    assert layout.count() == 2


def test_build_hbox() -> None:
    hbox = HBox("h")
    hbox.add(Component("x"))

    widget = build(hbox)

    assert isinstance(widget, QWidget)
    assert isinstance(widget.layout(), QHBoxLayout)


def test_build_grid_uses_cols() -> None:
    grid = Grid("g", cols=2)
    grid.add(Component("a"))
    grid.add(Component("b"))
    grid.add(Component("c"))

    widget = build(grid)

    assert isinstance(widget.layout(), QGridLayout)
    assert widget.layout().count() == 3


def test_bridge_emits_qt_signal(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    session = Session(vault.signal)
    bridge = Bridge(session)
    seen: list[object] = []
    bridge.changed.connect(seen.append)

    vault.put_block(Block(body=b"x"))

    assert len(seen) == 1
    bridge.close()
    vault.close()
