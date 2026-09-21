# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组件原子：最小可复用部件（声明 + 词汇元数据）。

`STYLABLE` 是可样式化属性、`STATES` 是可表达状态——主题 schema 据此校验。
Qt 实现在 `ui_tools/core/qt.py`；此处不依赖 Qt。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .component import Component

if TYPE_CHECKING:
    from collections.abc import Callable


def _default_row(item: object) -> str:
    return str(item)


class Label(Component):
    """文本标签。"""

    kind = "label"
    STYLABLE = frozenset({"color", "font_size", "font_weight", "align"})

    def __init__(self, text: str = "", *, name: str = "", **opts: Any) -> None:
        super().__init__(name, **opts)
        self.text = text


class Heading(Component):
    """标题 / 强调文本（比 `Label` 更重，用于品牌与区块标题）。"""

    kind = "heading"
    STYLABLE = frozenset({"color", "font_size", "font_weight", "align"})

    def __init__(self, text: str = "", *, name: str = "", **opts: Any) -> None:
        super().__init__(name, **opts)
        self.text = text


class Button(Component):
    """按钮。"""

    kind = "button"
    STYLABLE = frozenset({"background", "color", "border_color", "radius"})
    STATES = frozenset({"hover", "pressed", "disabled", "checked"})

    def __init__(self, text: str = "", *, name: str = "", **opts: Any) -> None:
        super().__init__(name, **opts)
        self.text = text
        self.clicked = self.ui_signal("clicked")


class Field(Component):
    """单行输入。"""

    kind = "field"
    STYLABLE = frozenset({"background", "color", "border_color", "radius", "padding"})
    STATES = frozenset({"focus", "disabled"})

    def __init__(
        self,
        text: str = "",
        *,
        placeholder: str = "",
        name: str = "",
        **opts: Any,
    ) -> None:
        super().__init__(name, **opts)
        self.text = text
        self.placeholder = placeholder
        self.text_changed = self.ui_signal("textChanged")


class Divider(Component):
    """分隔线。"""

    kind = "divider"
    STYLABLE = frozenset({"color", "thickness"})


class Chip(Component):
    """小标签 / 徽标。"""

    kind = "chip"
    STYLABLE = frozenset({"background", "color", "radius"})

    def __init__(self, text: str = "", *, name: str = "", **opts: Any) -> None:
        super().__init__(name, **opts)
        self.text = text


class List(Component):
    """列表（数据来自类型化 `Model`；`row` 决定行文本）。"""

    kind = "list"
    STYLABLE = frozenset({"background", "color"})

    def __init__(
        self,
        model: Any = None,
        *,
        row: Callable[[Any], str] | None = None,
        name: str = "",
        **opts: Any,
    ) -> None:
        super().__init__(name, **opts)
        self.model = model
        self.row: Callable[[Any], str] = row if row is not None else _default_row


__all__ = ["Button", "Chip", "Divider", "Field", "Heading", "Label", "List"]
