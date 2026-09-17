# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""原子组件：叶子控件，无联动业务，只发意图。

- `Label` / `Button` / `IconButton`：包一层对应 Qt 控件，附统一 `Component` API；
- `Field`（横向）/ `Section`（纵向）：直接继承布局原语，天然可组合。

联动一律交给上层的控制器，原子之间不互相连线。见 `rules/references/ui-boundary.md` §6。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..component import Component
from ..layout import HBox, VBox

if TYPE_CHECKING:
    from collections.abc import Callable


class Label(Component):
    """文本原子。"""

    STATES: ClassVar[frozenset[str]] = frozenset()
    STYLABLE: ClassVar[frozenset[str]] = Component.STYLABLE | {"font_size", "font_weight"}

    def __init__(self, text: str = "", *, role: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label = QLabel(text, self)
        if role:
            self._label.setObjectName(role)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._label)

    @property
    def control(self) -> QLabel:
        """内层 Qt 控件（需要精细控制时用）。"""
        return self._label

    @property
    def text(self) -> str:
        return self._label.text()

    @text.setter
    def text(self, value: str) -> None:
        self._label.setText(value)


class Button(Component):
    """按钮原子；点击以 ``clicked`` 发意图。"""

    clicked = Signal()

    def __init__(
        self,
        text: str = "",
        *,
        role: str = "",
        on_click: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._button = QPushButton(text, self)
        if role:
            self._button.setObjectName(role)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button)
        self._button.clicked.connect(self.clicked.emit)
        if on_click is not None:
            self.clicked.connect(on_click)

    @property
    def control(self) -> QPushButton:
        """内层 Qt 控件。"""
        return self._button

    @property
    def text(self) -> str:
        return self._button.text()

    @text.setter
    def text(self, value: str) -> None:
        self._button.setText(value)

    def set_enabled(self, *, enabled: bool) -> None:
        """启用 / 置灰。"""
        self._button.setEnabled(enabled)


class IconButton(Component):
    """纯图标按钮原子（字形 + 提示）；点击以 ``clicked`` 发意图。"""

    clicked = Signal()

    def __init__(
        self,
        glyph: str,
        *,
        tip: str = "",
        on_click: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._button = QToolButton(self)
        self._button.setText(glyph)
        self._button.setFont(QFont(self.theme.icon_font))
        if tip:
            self._button.setToolTip(tip)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button)
        self._button.clicked.connect(self.clicked.emit)
        if on_click is not None:
            self.clicked.connect(on_click)

    @property
    def control(self) -> QToolButton:
        """内层 Qt 控件。"""
        return self._button


class Field(HBox):
    """标签 + 单行输入；回车以 ``submitted`` 发意图。"""

    submitted = Signal(str)

    def __init__(
        self,
        label: str = "",
        *,
        placeholder: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent, spacing=8)
        self._label = Label(label)
        self._edit = QLineEdit()
        self._edit.setPlaceholderText(placeholder)
        self._edit.returnPressed.connect(self._on_submit)
        self.add(self._label)
        self.add(self._edit, stretch=1)

    @property
    def edit(self) -> QLineEdit:
        """内层输入控件。"""
        return self._edit

    @property
    def value(self) -> str:
        return self._edit.text()

    @value.setter
    def value(self, text: str) -> None:
        self._edit.setText(text)

    def _on_submit(self) -> None:
        self.submitted.emit(self._edit.text())


class Section(VBox):
    """带标题的分区容器；`body` 放内容。"""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=8)
        self._header = Label(title, role="SectionTitle")
        self._body = VBox()
        self.add(self._header)
        self.add(self._body, stretch=1)

    @property
    def body(self) -> VBox:
        """内容容器。"""
        return self._body

    def set_title(self, text: str) -> None:
        """更新分区标题。"""
        self._header.text = text


class Divider(Component):
    """分隔线（横 / 纵）；本身即被样式化的载体。"""

    STATES: ClassVar[frozenset[str]] = frozenset()
    STYLABLE: ClassVar[frozenset[str]] = Component.STYLABLE | {"background"}

    def __init__(self, *, vertical: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if vertical:
            self.setFixedWidth(1)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        else:
            self.setFixedHeight(1)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


class Chip(Component):
    """标签 / 胶囊按钮；点击以 ``clicked`` 发意图。"""

    clicked = Signal()

    def __init__(
        self,
        text: str = "",
        *,
        on_click: Callable[[], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._button = QPushButton(text, self)
        self._button.setFlat(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._button)
        self._button.clicked.connect(self.clicked.emit)
        if on_click is not None:
            self.clicked.connect(on_click)

    @property
    def control(self) -> QPushButton:
        """内层 Qt 控件。"""
        return self._button

    @property
    def text(self) -> str:
        return self._button.text()

    @text.setter
    def text(self, value: str) -> None:
        self._button.setText(value)


class ToggleSwitch(Component):
    """布尔开关；变化以 ``toggled(bool)`` 发意图。"""

    toggled = Signal(bool)

    def __init__(self, *, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._check = QCheckBox(self)
        self._check.setChecked(checked)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._check)
        self._check.toggled.connect(self.toggled.emit)

    @property
    def control(self) -> QCheckBox:
        """内层 Qt 控件。"""
        return self._check

    @property
    def checked(self) -> bool:
        return self._check.isChecked()

    @checked.setter
    def checked(self, value: bool) -> None:
        self._check.setChecked(value)


__all__ = [
    "Button",
    "Chip",
    "Divider",
    "Field",
    "IconButton",
    "Label",
    "Section",
    "ToggleSwitch",
]
