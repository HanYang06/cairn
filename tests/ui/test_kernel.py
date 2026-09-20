# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from ui_tools.component import Component
from ui_tools.core import (
    Compiler,
    LayoutError,
    UiError,
    registered_kinds,
    vocabulary,
)
from ui_tools.layout import Grid, VBox


def test_kinds_registered() -> None:
    kinds = registered_kinds()

    assert kinds["vbox"] is VBox
    assert kinds["grid"] is Grid
    assert kinds["component"] is Component


def test_duplicate_kind_raises() -> None:
    with pytest.raises(LayoutError, match="节点类型冲突"):

        class Clash(Component):
            kind = "component"


def test_node_parent_path_and_walk() -> None:
    root = VBox("root")
    body = Grid("body")
    leaf = Component("editor")

    root.add(body)
    body.add(leaf)

    assert body.parent is root
    assert leaf.path() == "app.root.body.editor"
    assert [node.name for node in root.walk()] == ["root", "body", "editor"]


def test_compiler_dispatches_by_kind() -> None:
    compiler = Compiler()
    compiler.register("vbox", lambda _node, children: ("vbox", children))
    compiler.register("component", lambda node, _children: node.name)

    root = VBox("root")
    root.add(Component("a"))
    root.add(Component("b"))

    assert compiler.compile(root) == ("vbox", ["a", "b"])
    assert compiler.kinds() == ["component", "vbox"]


def test_compiler_unknown_kind_raises() -> None:
    compiler = Compiler()

    with pytest.raises(UiError, match="未注册的翻译器"):
        compiler.compile(VBox("root"))


def test_vocabulary_shape() -> None:
    vocab = vocabulary()

    assert "component" in vocab
    assert set(vocab["component"]) == {"stylable", "states"}
