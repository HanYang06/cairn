# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""编译层测试：布局 / 组件 / 样式 / 逃生舱 / 错误路径（离屏）。"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QLabel, QPushButton, QStackedWidget, QWidget

from cairn.ui.decl import (
    Button,
    Compiler,
    Component,
    Display,
    Grid,
    HBox,
    Label,
    Node,
    NodeError,
    Page,
    Placement,
    Raw,
    RegistryError,
    Scope,
    Stack,
    Table,
    VBox,
    component_key,
    layout_key,
    register,
    registered,
    token,
)
from cairn.ui.decl.components import _build_label
from cairn.ui.decl.layouts import _build_vbox
from cairn.ui.theme import DARK, LIGHT

pytestmark = pytest.mark.usefixtures("qapp")


def _compile(node: Node) -> QWidget:
    return Compiler(Scope(LIGHT)).build(node)


def test_compile_vbox_with_label() -> None:
    layout = VBox()
    layout.add(Label("hi"))
    widget = _compile(layout)
    label = widget.findChild(QLabel)
    assert label is not None
    assert label.text() == "hi"


def test_compile_hbox() -> None:
    layout = HBox(spacing=4)
    layout.add(Label("a"))
    layout.add(Label("b"))
    assert len(_compile(layout).findChildren(QLabel)) == 2


def test_compile_grid() -> None:
    grid = Grid()
    grid.add(Label("a"), at=(0, 0))
    grid.add(Label("b"), at=(1, 0))
    assert len(_compile(grid).findChildren(QLabel)) == 2


def test_compile_stack() -> None:
    stack = Stack()
    stack.add(Label("a"))
    stack.add(Label("b"))
    widget = _compile(stack)
    assert isinstance(widget, QStackedWidget)
    assert widget.count() == 2


def test_compile_table() -> None:
    table = Table(2, 2)
    table.add(Label("a"), at=(0, 0))
    assert _compile(table).findChild(QLabel) is not None


def test_button_click_emits_intent() -> None:
    seen: list[int] = []
    button = Button("go").on("clicked", lambda: seen.append(1))
    widget = _compile(button)
    assert isinstance(widget, QPushButton)
    widget.click()
    assert seen == [1]


def test_style_resolved_and_applied() -> None:
    widget = _compile(Label("x", style={"color": token("text")}))
    assert widget.objectName().startswith("decl-")
    assert LIGHT.text in widget.styleSheet()


def test_node_scope_overrides_ambient_theme() -> None:
    widget = _compile(Label("x", style={"color": token("text")}, scope=Scope(DARK)))
    assert DARK.text in widget.styleSheet()


def test_page_scope_inherited_by_children() -> None:
    page = Page(route="p", scope=Scope(DARK))
    box = VBox()
    box.add(Label("x", style={"color": token("text")}))
    page.add(box)
    widget = _compile(page)
    label = widget.findChild(QLabel)
    assert label is not None
    assert DARK.text in label.styleSheet()


def test_component_conf_applied() -> None:
    widget = _compile(Label("x", tooltip="提示", enabled=False))
    assert widget.toolTip() == "提示"
    assert widget.isEnabled() is False


def test_raw_escape_hatch() -> None:
    widget = _compile(Raw(lambda: QLabel("raw")))
    assert isinstance(widget, QLabel)
    assert widget.text() == "raw"


def test_bare_display_builds_and_mounts_children() -> None:
    display = Display()
    display.add(Label("x"))
    assert _compile(display).findChild(QLabel) is not None


def test_placement_property_recorded() -> None:
    assert _compile(Label("x")).property("cairnPlacement") == Placement.FLOW.value


def test_page_without_layout_errors() -> None:
    with pytest.raises(NodeError):
        _compile(Page(route="x"))


def test_page_with_layout_builds() -> None:
    page = Page(route="x", title="X")
    page.add(VBox())
    assert _compile(page) is not None


def test_compile_rejects_bare_node() -> None:
    with pytest.raises(NodeError):
        _compile(Node())


class Unregistered(Component):
    kind = "unregistered-test"


def test_missing_builder_errors() -> None:
    with pytest.raises(RegistryError):
        _compile(Unregistered())


def test_builder_rejects_wrong_node_type() -> None:
    compiler = Compiler(Scope(LIGHT))
    with pytest.raises(RegistryError):
        _build_label(Button("x"), compiler)
    with pytest.raises(NodeError):
        _build_vbox(Label("x"), compiler)


def test_registered_contains_builtins() -> None:
    keys = registered()
    assert component_key("label") in keys
    assert layout_key("vbox") in keys


def test_duplicate_registration_errors() -> None:
    key = component_key("dup-test")
    register(key)(lambda _node, _compiler: QLabel())
    with pytest.raises(RegistryError):
        register(key)(lambda _node, _compiler: QLabel())
