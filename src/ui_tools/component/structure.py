# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""结构件：壳区域与卡片舞台的**声明件**（Qt 翻译在 `core/qt.py`）。

只声明形态与数据来源；子件由作者放入（布局 / 部件不自包含）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .component import Component

if TYPE_CHECKING:
    from collections.abc import Callable

    from ..core.model import Model


def _empty(_item: object) -> str:
    return ""


class CardStage(Component):
    """卡片舞台：`Model` → 卡片 / 详细两种密度（`badge` 决定着色）。"""

    kind = "stage"

    def __init__(  # noqa: PLR0913 — 提取器 + 能力声明是显式参数面，均有默认值
        self,
        model: Model[Any] | None = None,
        *,
        title: Callable[[Any], str] | None = None,
        preview: Callable[[Any], str] | None = None,
        meta: Callable[[Any], str] | None = None,
        badge: Callable[[Any], str] | None = None,
        density: str = "cards",
        name: str = "stage",
        stretch: bool = True,
        **opts: Any,
    ) -> None:
        super().__init__(name, stretch=stretch, **opts)
        self.model = model
        self.title: Callable[[Any], str] = title or str
        self.preview: Callable[[Any], str] = preview or _empty
        self.meta: Callable[[Any], str] = meta or _empty
        self.badge: Callable[[Any], str] = badge or _empty
        self.density = density


class Surface(Component):
    """带外观的通用容器（背景 / 圆角 / 边框 / 可选投影）；`orientation` 定横竖。"""

    kind = "surface"
    STYLABLE = frozenset({"background", "border_color", "radius"})

    def __init__(
        self,
        *,
        orientation: str = "v",
        elevated: bool = False,
        name: str = "surface",
        **opts: Any,
    ) -> None:
        super().__init__(name, **opts)
        self.orientation = orientation
        self.elevated = elevated


__all__ = ["CardStage", "Surface"]
