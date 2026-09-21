# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt 翻译器：把声明树编译成 QWidget 树。

按 `kind` 注册翻译器到通用 `Compiler`；每个控件打 `cairnClass`（主题选择器命中）、
`cairnStretch`（弹性权重）与 `objectName`（定位）。内核其余部分不感知 Qt。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .cardview import CardStageView
from .compile import Compiler
from .errors import UiError
from .qtmodel import QtListModel
from .theme import Theme

if TYPE_CHECKING:
    from .app import App
    from .bind import Binding
    from .node import Node


def build_compiler(theme: Theme | None = None) -> Compiler:
    """装配一套 Widgets 翻译器（卡片委托 / 投影需要主题令牌）。"""
    active = theme or Theme()
    compiler = Compiler()
    compiler.register("page", _page)
    compiler.register("node", _vbox)
    compiler.register("layout", _vbox)
    compiler.register("vbox", _vbox)
    compiler.register("hbox", _hbox)
    compiler.register("grid", _grid)
    compiler.register("split", _split)
    compiler.register("stack", _stack)
    compiler.register("component", _vbox)
    compiler.register("slot", _slot)
    compiler.register("label", _label)
    compiler.register("heading", _label)
    compiler.register("button", _button)
    compiler.register("field", _field)
    compiler.register("divider", _divider)
    compiler.register("chip", _chip)
    compiler.register("list", _list)

    def surface_translator(node: Node, children: list[object]) -> object:
        return _surface(node, children, active)

    def stage_translator(node: Node, children: list[object]) -> object:
        return _stage(node, children, active)

    compiler.register("surface", surface_translator)
    compiler.register("stage", stage_translator)
    return compiler


def build(node: Node, theme: Theme | None = None) -> object:
    """把一棵声明树编译为 Qt 对象。"""
    return build_compiler(theme).compile(node)


class WindowHost:
    """把 `App` 的根结构编译成窗口。"""

    def __init__(self, app: App) -> None:
        self.app = app
        self.theme = app.theme
        self.compiler = build_compiler(self.theme)
        self.window = self._build()
        self._connect_bindings()

    def _build(self) -> QMainWindow:
        window = QMainWindow()
        central = self.compiler.compile(self.app.root)
        if not isinstance(central, QWidget):
            raise UiError("根节点未编译为控件")
        central.setProperty("cairnClass", "shell")
        central.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, on=True)
        layout = central.layout()
        if layout is not None:
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(8)
        window.setCentralWidget(central)
        return window

    def _connect_bindings(self) -> None:
        for binding in self.app.bind.compile():
            self._connect(binding)
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


def build_window(app: App) -> QMainWindow:
    """把 `App` 的根结构落成窗口。"""
    return WindowHost(app).window


def run(
    app: App,
    *,
    title: str = "Cairn",
    size: tuple[int, int] = (1200, 780),
) -> int:
    """启动 Qt 事件循环：套主题 → 建窗 → 显示 → `exec`（App 级入口用，一行搞定）。"""
    qapp = QApplication.instance() or QApplication([])
    app.theme.apply(qapp)
    window = build_window(app)
    window.setWindowTitle(title)
    window.resize(*size)
    window.show()
    return qapp.exec()


def _tag(widget: QWidget, node: Node) -> QWidget:
    widget.setProperty("cairnClass", node.kind)
    widget.setProperty("cairnStretch", node.stretch)
    widget.setObjectName(node.name or node.kind)
    node.bind_widget(widget)
    return widget


def _weight(widget: QWidget) -> int:
    return 1 if widget.property("cairnStretch") else 0


def _shadow(widget: QWidget, theme: Theme, *, blur: float, dy: float) -> None:
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setOffset(0.0, dy)
    color = QColor(theme.token("shadow_color", "#000000"))
    color.setAlpha(int(theme.token("shadow_alpha", "110")))
    effect.setColor(color)
    widget.setGraphicsEffect(effect)


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
            layout.addWidget(child, _weight(child))
    return widget


def _slot(node: Node, children: list[object]) -> QWidget:
    """槽：只管自己的行为（弹性由父布局读 `cairnStretch`；滚动 / 对齐 / 隐藏在此处理）。

    默认内容**撑满**槽；`align="top"` 则按自身尺寸顶对齐（如导航条目）。
    """
    widget = _tag(QWidget(), node)
    layout = QVBoxLayout(widget)
    top = getattr(node, "align", None) == "top"
    for child in children:
        if isinstance(child, QWidget):
            layout.addWidget(child, 0 if top else 1)
    if top:
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    if getattr(node, "scroll", False):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        area.setWidget(widget)
        area.setProperty("cairnClass", "scroll")
        area.setObjectName(node.name or "scroll")
        node.bind_widget(area)
        widget = area
    if getattr(node, "hidden", False):
        widget.setVisible(False)
    return widget


def _surface(node: Node, children: list[object], theme: Theme) -> QWidget:
    frame = _tag(QFrame(), node)
    frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, on=True)
    layout: QBoxLayout = (
        QHBoxLayout(frame) if getattr(node, "orientation", "v") == "h" else QVBoxLayout(frame)
    )
    layout.setContentsMargins(12, 8, 12, 8)
    layout.setSpacing(10)
    for child in children:
        if isinstance(child, QWidget):
            layout.addWidget(child, _weight(child))
    if getattr(node, "elevated", False):
        _shadow(frame, theme, blur=28.0, dy=6.0)
    return frame


def _stage(node: Node, children: list[object], theme: Theme) -> QWidget:
    del children
    model = getattr(node, "model", None)
    if model is None:
        raise UiError("stage 缺少 model")
    view = CardStageView(
        model,
        theme,
        title=getattr(node, "title", str),
        preview=getattr(node, "preview", lambda _x: ""),
        meta=getattr(node, "meta", lambda _x: ""),
        badge=getattr(node, "badge", lambda _x: ""),
        density=str(getattr(node, "density", "cards")),
    )
    return _tag(view, node)


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


def _list(node: Node, _children: list[object]) -> QWidget:
    view = QListView()
    model = getattr(node, "model", None)
    if model is not None:
        row = getattr(node, "row", None) or str
        view.setModel(QtListModel(model, row))
    return _tag(view, node)


__all__ = ["WindowHost", "build", "build_compiler", "build_window", "run"]
