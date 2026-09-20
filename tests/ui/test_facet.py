# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from ui_tools.component import Component
from ui_tools.core import App, Facet, LayoutError
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


def test_app_mount_and_navigate() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    facet = Facet(FakeDomain())
    page = Page("edit")
    facet.page(page, "edit")

    app.mount(facet)

    host = [placed.component for placed in app.layout.content.children()]
    assert app.facets() == [facet]
    assert facet.root in host
    assert page in host
    assert app.navigate("edit") is page
    assert app.active is page


def test_navigate_unknown_route_raises() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    with pytest.raises(Exception, match="未挂载的路由"):
        app.navigate("nope")


def test_slot_capacity_enforced() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    app.layout.inspector.add(FakeButton("a"))

    with pytest.raises(LayoutError):
        app.layout.inspector.add(FakeButton("b"))


def test_super_layout_not_addable() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    with pytest.raises(LayoutError):
        app.layout.add(FakeButton("x"))
