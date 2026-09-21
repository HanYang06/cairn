# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from ui_tools.component import Component
from ui_tools.core import App, Facet, LayoutError, Node, Slot, UiError, UiSignal
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


def test_slot_accepts_explicit_addable() -> None:
    slot = Slot("s", locked=True, addable=True)  # 显式覆盖锁定默认
    slot.add(FakeButton("x"))
    assert len(slot.children()) == 1

    locked = Slot("l", addable=False)
    with pytest.raises(LayoutError):
        locked.add(FakeButton("y"))


def test_app_rejects_duplicate_slot_expects() -> None:
    app = App(session=None)  # type: ignore[arg-type]
    app.root.add(Slot("a", expects="page"))
    app.root.add(Slot("b", expects="page"))

    with pytest.raises(UiError, match="同一部件"):
        app.add(Facet(FakeDomain()))


def test_page_reregister_cleans_stale_routes() -> None:
    facet = Facet(FakeDomain())
    first = Page("one")
    second = Page("two")
    facet.page(first, "edit")
    facet.page(first, "view")  # 同一页换路由
    facet.page(second, "edit")  # 路由被别的页接管

    assert facet.pages() == {first: "view", second: "edit"}
    assert facet.navigate("view") is first
    assert facet.navigate("edit") is second
    with pytest.raises(UiError):
        facet.navigate("gone")


def test_compile_bindings_skips_root_page() -> None:
    facet = Facet(FakeDomain())
    facet.page(facet.root, "root")
    facet.root.bind.add(UiSignal("clicked"), lambda: None)

    assert len(facet.compile_bindings()) == 1


def test_node_reparent_detaches_from_old_parent() -> None:
    first = Node("p1")
    second = Node("p2")
    child = FakeButton("c")

    first.add(child)
    second.add(child)

    assert first.children() == []
    assert [placed.component for placed in second.children()] == [child]
    assert child.parent is second


def test_page_clear_keeps_root_layout() -> None:
    page = Page("p")
    layout = page.layout
    page.add(FakeButton("a"))

    page.clear()

    assert page.layout is layout
    assert page.layout.children() == []


def test_page_set_replaces_root_layout() -> None:
    page = Page("p")
    old = page.layout

    new = page.set(Grid, rows=1, cols=1)

    assert page.layout is new
    assert [placed.component for placed in page.children()] == [new]
    assert old.parent is None
