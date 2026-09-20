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

from ..page import Page
from .compile import Compiler
from .errors import UiError
from .node import Node

if TYPE_CHECKING:
    from .app import App
    from .bind import Binding


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


class WindowHost:
    """把 `App` 落成窗口并托管页面切换（路由 → Qt 内容栈）。"""

    def __init__(self, app: App) -> None:
        self.app = app
        self.compiler = build_compiler()
        self.stack = QStackedWidget()
        self._index: dict[Page, int] = {}
        self.window = self._build()
        self._connect_bindings()

    def show(self, route: object) -> Page:
        """路由到某页并在内容区切换。"""
        page = self.app.navigate(route)
        index = self._index.get(page)
        if index is None:
            raise UiError(f"页面未挂载到窗口: {page!r}")
        self.stack.setCurrentIndex(index)
        return page

    def _build(self) -> QMainWindow:
        app = self.app
        window = QMainWindow()
        central = QWidget()
        window.setCentralWidget(central)
        column = QVBoxLayout(central)
        column.addWidget(self._region(app.layout.titlebar))
        middle = QHBoxLayout()
        middle.addWidget(self._region(app.layout.navigator))
        middle.addWidget(self._content(), 1)
        middle.addWidget(self._region(app.layout.inspector))
        column.addLayout(middle, 1)
        column.addWidget(self._region(app.layout.statusbar))
        return window

    def _region(self, region: Node) -> QWidget:
        container = _tag(QWidget(), region)
        layout = QVBoxLayout(container)
        for placed in region.children():
            if isinstance(placed.component, Node):
                widget = self.compiler.compile(placed.component)
                if isinstance(widget, QWidget):
                    layout.addWidget(widget)
        return container

    def _connect_bindings(self) -> None:
        for facet in self.app.facets():
            for binding in facet.compile_bindings():
                self._connect(binding)

    def _connect(self, binding: Binding) -> None:
        source = binding.source
        owner = getattr(source, "owner", None)
        widget = getattr(owner, "widget", None)
        name = str(getattr(source, "name", ""))
        if widget is None or not name:
            return
        signal = getattr(widget, name, None)
        if signal is not None and hasattr(signal, "connect"):
            signal.connect(binding.target)

    def _content(self) -> QWidget:
        content = self.app.layout.content
        for placed in content.children():
            if not isinstance(placed.component, Node):
                continue
            widget = self.compiler.compile(placed.component)
            if isinstance(widget, QWidget):
                self.stack.addWidget(widget)
                if isinstance(placed.component, Page):
                    self._index[placed.component] = self.stack.count() - 1
        return _tag(self.stack, content)


def build_window(app: App) -> QMainWindow:
    """把 `App` 的根壳落成窗口：标题栏 / 导航+内容+检查器 / 状态栏。"""
    return WindowHost(app).window


def _tag(widget: QWidget, node: Node) -> QWidget:
    widget.setProperty("cairnClass", node.kind)
    node.bind_widget(widget)
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


__all__ = ["WindowHost", "build", "build_compiler", "build_window"]
