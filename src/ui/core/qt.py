# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt 翻译器：把声明树编译成 QWidget 树（M1 最小实现）。

按 `kind` 注册翻译器到通用 `Compiler`；每个控件打 `cairnClass` 动态属性，
供主题选择器 `widget.<kind>[:state]` 命中。内核其余部分不感知 Qt。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .compile import Compiler
from .node import Node

if TYPE_CHECKING:
    from .app import App


def build_compiler() -> Compiler:
    """装配一套 Widgets 翻译器。"""
    compiler = Compiler()
    compiler.register("page", _page)
    compiler.register("layout", _vbox)
    compiler.register("vbox", _vbox)
    compiler.register("hbox", _hbox)
    compiler.register("grid", _grid)
    compiler.register("split", _split)
    compiler.register("stack", _stack)
    compiler.register("component", _vbox)
    compiler.register("label", _label)
    compiler.register("button", _button)
    compiler.register("field", _field)
    compiler.register("divider", _divider)
    compiler.register("chip", _chip)
    return compiler


def build(node: Node) -> object:
    """把一棵声明树编译为 Qt 对象。"""
    return build_compiler().compile(node)


def build_window(app: App) -> QMainWindow:
    """把 `App` 的根壳落成窗口：标题栏 / 导航+内容+检查器 / 状态栏。"""
    compiler = build_compiler()
    window = QMainWindow()
    central = QWidget()
    window.setCentralWidget(central)
    column = QVBoxLayout(central)
    column.addWidget(_region(compiler, app.layout.titlebar))
    middle = QHBoxLayout()
    middle.addWidget(_region(compiler, app.layout.navigator))
    middle.addWidget(_content(compiler, app), 1)
    middle.addWidget(_region(compiler, app.layout.inspector))
    column.addLayout(middle, 1)
    column.addWidget(_region(compiler, app.layout.statusbar))
    return window


def _region(compiler: Compiler, region: Node) -> QWidget:
    container = _tag(QWidget(), region)
    layout = QVBoxLayout(container)
    for placed in region.children():
        if isinstance(placed.component, Node):
            widget = compiler.compile(placed.component)
            if isinstance(widget, QWidget):
                layout.addWidget(widget)
    return container


def _content(compiler: Compiler, app: App) -> QWidget:
    stack = QStackedWidget()
    for placed in app.layout.content.children():
        if isinstance(placed.component, Node):
            widget = compiler.compile(placed.component)
            if isinstance(widget, QWidget):
                stack.addWidget(widget)
    return _tag(stack, app.layout.content)


def _tag(widget: QWidget, node: Node) -> QWidget:
    widget.setProperty("cairnClass", node.kind)
    return widget


def _page(node: Node, children: list[object]) -> object:
    if len(children) == 1 and isinstance(children[0], QWidget):
        return children[0]
    return _box(node, QVBoxLayout(), children)


def _vbox(node: Node, children: list[object]) -> QWidget:
    return _box(node, QVBoxLayout(), children)


def _hbox(node: Node, children: list[object]) -> QWidget:
    return _box(node, QHBoxLayout(), children)


def _box(node: Node, layout: QBoxLayout, children: list[object]) -> QWidget:
    widget = _tag(QWidget(), node)
    widget.setLayout(layout)
    for child in children:
        if isinstance(child, QWidget):
            layout.addWidget(child)
    return widget


def _grid(node: Node, children: list[object]) -> QWidget:
    widget = _tag(QWidget(), node)
    layout = QGridLayout(widget)
    cols = int(node.options.get("cols", 1) or 1)
    for index, child in enumerate(children):
        if isinstance(child, QWidget):
            layout.addWidget(child, index // cols, index % cols)
    return widget


def _split(node: Node, children: list[object]) -> QWidget:
    splitter = QSplitter(Qt.Orientation.Horizontal)
    for child in children:
        if isinstance(child, QWidget):
            splitter.addWidget(child)
    return _tag(splitter, node)


def _stack(node: Node, children: list[object]) -> QWidget:
    stack = QStackedWidget()
    for child in children:
        if isinstance(child, QWidget):
            stack.addWidget(child)
    return _tag(stack, node)


def _label(node: Node, _children: list[object]) -> QWidget:
    return _tag(QLabel(str(getattr(node, "text", ""))), node)


def _button(node: Node, _children: list[object]) -> QWidget:
    return _tag(QPushButton(str(getattr(node, "text", ""))), node)


def _field(node: Node, _children: list[object]) -> QWidget:
    edit = QLineEdit(str(getattr(node, "text", "")))
    placeholder = str(getattr(node, "placeholder", ""))
    if placeholder:
        edit.setPlaceholderText(placeholder)
    return _tag(edit, node)


def _divider(node: Node, _children: list[object]) -> QWidget:
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.HLine)
    return _tag(frame, node)


def _chip(node: Node, _children: list[object]) -> QWidget:
    return _tag(QLabel(str(getattr(node, "text", ""))), node)


__all__ = ["build", "build_compiler", "build_window"]
