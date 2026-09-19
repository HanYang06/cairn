# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""节点组合测试：交替规则、意图边、页面身份。"""

from __future__ import annotations

import pytest

from cairn.ui.decl import (
    Component,
    Display,
    Grid,
    Label,
    Node,
    NodeError,
    Page,
    Placement,
    VBox,
)


def test_placement_default_is_flow() -> None:
    assert VBox().placement is Placement.FLOW


def test_layout_rejects_non_display() -> None:
    with pytest.raises(NodeError):
        VBox().add(Node())  # type: ignore[arg-type]


def test_layout_accepts_component_and_page() -> None:
    layout = VBox()
    assert layout.add(Label("x")) is not None
    assert layout.add(Page(route="p")) is not None


def test_display_rejects_page() -> None:
    with pytest.raises(NodeError):
        Display().add(Page(route="p"))


def test_display_rejects_bare_node() -> None:
    with pytest.raises(NodeError):
        Display().add(Node())


def test_display_accepts_layout_and_component() -> None:
    display = Display()
    assert display.add(VBox()) is not None
    assert display.add(Label("x")) is not None


def test_grid_requires_slot() -> None:
    with pytest.raises(NodeError):
        Grid().add(Label("x"))


def test_intents_are_edges() -> None:
    seen: list[int] = []
    node = Node().on("tap", lambda: seen.append(1))
    assert node.emit("tap") is True
    assert seen == [1]
    assert node.emit("missing") is False


def test_page_identity() -> None:
    page = Page(route="notes", title="笔记")
    assert page.role == "page"
    assert page.route == "notes"
    assert page.title == "笔记"


def test_component_role() -> None:
    assert Component().role == "component"
