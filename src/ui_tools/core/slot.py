# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""槽位：App 结构里一个**命名的填充点**。

槽只管**自己的行为**（弹性 / 滚动 / 锁死 / 隐藏 / 容量），**不管内容怎么显示**——
内容怎么显示是组件自己的事。`expects` 声明它等 Facet 的哪个命名部件（App 的翻译依据）。
"""

from __future__ import annotations

from typing import Any

from .node import Node


class Slot(Node):
    """命名槽位。"""

    kind = "slot"

    def __init__(  # noqa: PLR0913 — 槽的行为是显式参数面，均有默认值
        self,
        name: str = "",
        *,
        expects: str | None = None,
        scroll: bool = False,
        hidden: bool = False,
        locked: bool = False,
        align: str | None = None,
        stretch: bool = False,
        capacity: int | None = None,
        addable: bool | None = None,
        **opts: Any,
    ) -> None:
        resolved = (not locked) if addable is None else addable
        super().__init__(name, addable=resolved, capacity=capacity, stretch=stretch, **opts)
        self.expects = expects
        self.scroll = scroll
        self.hidden = hidden
        self.locked = locked
        self.align = align


__all__ = ["Slot"]
