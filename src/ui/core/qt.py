# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt 翻译器：把声明树编译成 QWidget 树（M1 最小实现）。

按 `kind` 注册翻译器到通用 `Compiler`；内核其余部分不感知 Qt。
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
    QPushButton,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .compile import Compiler

if TYPE_CHECKING:
    from .node import Node


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


def _page(_node: Node, children: list[object]) -> object:
    if len(children) == 1 and isinstance(children[0], QWidget):
        return children[0]
    return _box(QVBoxLayout(), children)


def _vbox(_node: Node, children: list[object]) -> QWidget:
    return _box(QVBoxLayout(), children)


def _hbox(_node: Node, children: list[object]) -> QWidget:
    return _box(QHBoxLayout(), children)


def _box(layout: QBoxLayout, children: list[object]) -> QWidget:
    widget = QWidget()
    widget.setLayout(layout)
    for child in children:
        if isinstance(child, QWidget):
            layout.addWidget(child)
    return widget


def _grid(node: Node, children: list[object]) -> QWidget:
    widget = QWidget()
    layout = QGridLayout(widget)
    cols = int(node.options.get("cols", 1) or 1)
    for index, child in enumerate(children):
        if isinstance(child, QWidget):
            layout.addWidget(child, index // cols, index % cols)
    return widget


def _split(_node: Node, children: list[object]) -> QWidget:
    splitter = QSplitter(Qt.Orientation.Horizontal)
    for child in children:
        if isinstance(child, QWidget):
            splitter.addWidget(child)
    return splitter


def _stack(_node: Node, children: list[object]) -> QWidget:
    stack = QStackedWidget()
    for child in children:
        if isinstance(child, QWidget):
            stack.addWidget(child)
    return stack


def _label(node: Node, _children: list[object]) -> QWidget:
    return QLabel(str(getattr(node, "text", "")))


def _button(node: Node, _children: list[object]) -> QWidget:
    return QPushButton(str(getattr(node, "text", "")))


def _field(node: Node, _children: list[object]) -> QWidget:
    edit = QLineEdit(str(getattr(node, "text", "")))
    placeholder = str(getattr(node, "placeholder", ""))
    if placeholder:
        edit.setPlaceholderText(placeholder)
    return edit


def _divider(_node: Node, _children: list[object]) -> QWidget:
    frame = QFrame()
    frame.setFrameShape(QFrame.Shape.HLine)
    return frame


def _chip(node: Node, _children: list[object]) -> QWidget:
    chip = QLabel(str(getattr(node, "text", "")))
    chip.setProperty("cairnClass", "chip")
    return chip


__all__ = ["build", "build_compiler"]
