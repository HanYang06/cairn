# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from ui_tools.component import Component
from ui_tools.core import App, Facet, LayoutError, Slot
from ui_tools.layout import Grid
from ui_tools.page import Page


class FakeDomain:
    def __init__(self) -> None:
        self.saved = 0

    def save(self) -> None:
        self.saved += 1


class FakeButton(Component):
    pass


def test_facet_page_registry_and_route() -> None:
    facet = Facet(FakeDomain())
    page = Page("edit", title="编辑")

    facet.page(page, "edit")

    assert facet.pages() == {page: "edit"}
    assert facet.navigate("edit") is page


def test_facet_bind_and_conf() -> None:
    facet = Facet(FakeDomain())
    button = FakeButton("save")

    facet.bind.add(button, facet.domain.save)
    facet.conf.attr.set("editor.font.size", 14)
    facet.conf.theme.set("token.accent", "#122314")

    assert len(facet.bind.items()) == 1
    assert facet.conf.attr.get("editor.font.size") == 14
    assert facet.conf.theme.get("token.accent") == "#122314"


def test_facet_set_layout_and_add() -> None:
    facet = Facet(FakeDomain())

    layout = facet.set(Grid, rows=2, cols=2)
    facet.add(FakeButton("editor"), at=(0, 0))

    assert facet.root.layout is layout
    assert layout.options == {"rows": 2, "cols": 2}
    assert len(layout.children()) == 1


def test_facet_parts_default_page() -> None:
    facet = Facet(FakeDomain())

    assert facet.parts() == {"page": facet.root}


def test_app_add_fills_matching_slots() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    slot = app.root.add(Slot("main", expects="page"))
    facet = Facet(FakeDomain())

    app.add(facet)

    assert app.facets() == [facet]
    assert facet.root in [placed.component for placed in slot.children()]


def test_slot_capacity_enforced() -> None:
    slot = Slot("main", capacity=1)
    slot.add(FakeButton("a"))

    with pytest.raises(LayoutError):
        slot.add(FakeButton("b"))


def test_slot_locked_rejects_add() -> None:
    slot = Slot("fixed", locked=True)

    with pytest.raises(LayoutError):
        slot.add(FakeButton("x"))
