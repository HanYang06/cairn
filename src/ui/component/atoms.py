# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组件原子：最小可复用部件（声明 + 词汇元数据）。

`STYLABLE` 是可样式化属性、`STATES` 是可表达状态——主题 schema 据此校验。
Qt 实现在 `ui/core/qt.py`；此处不依赖 Qt。
"""

from __future__ import annotations

from typing import Any

from .component import Component


class Label(Component):
    """文本标签。"""

    kind = "label"
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


__all__ = ["Button", "Chip", "Divider", "Field", "Label"]
