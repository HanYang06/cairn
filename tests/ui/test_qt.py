# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core import Vault
from core.storage import Block
from ui_tools.component import Button, Component, Label
from ui_tools.core import App, Facet, Slot
from ui_tools.core.bridge import Bridge
from ui_tools.core.qt import WindowHost, build, build_window
from ui_tools.core.session import Session
from ui_tools.layout import Grid, HBox, VBox
from ui_tools.page import Page

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


class _Domain:
    pass


def test_build_window_root() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    app.root.add(HBox("body"))

    window = build_window(app)

    assert isinstance(window, QMainWindow)
    assert window.centralWidget() is not None


def test_slot_fills_facet_page() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    slot = app.root.add(Slot("main", expects="page"))
    facet = Facet(_Domain(), name="note")
    facet.set(VBox)
    facet.add(Label("hi"))

    app.add(facet)

    assert facet.root in [placed.component for placed in slot.children()]


def test_button_binding_clicks() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    app.root.add(Slot("main", expects="page"))
    facet = Facet(_Domain(), name="demo")
    facet.set(VBox)
    button = Button("go")
    calls: list[int] = []
    facet.bind.add(button.clicked, lambda: calls.append(1))
    facet.add(button)
    app.add(facet)

    host = WindowHost(app)
    qt_button = host.window.findChild(QPushButton)
    assert qt_button is not None
    qt_button.click()

    assert calls == [1]


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


def test_scroll_slot_keeps_stretch() -> None:
    slot = Slot("nav", stretch=True, scroll=True)
    slot.add(Label("hi"))

    widget = build(slot)

    assert widget.property("cairnStretch") is True
