# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""声明节点：UI 描述树的通用基元。

一个节点 = 名称 + 配置 + 子件 + **能力声明**（可增 / 弹性 / 可变量 / 容量 / 动作）。
布局、组件、页面都是它的子类；能力声明是我们在 Qt 之上加的第一层。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .conf import Conf
from .errors import LayoutError

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class Placed:
    """一个放置结果：子件 + 位置（有格 / 序的布局才用）。"""

    component: object
    at: object | None = None


class Node:
    """声明节点基类。"""

    kind: str = "node"

    def __init__(  # noqa: PLR0913 — 能力声明是显式参数面，均有默认值
        self,
        name: str = "",
        *,
        addable: bool = True,
        capacity: int | None = None,
        stretch: bool = False,
        variable: bool = True,
        actions: Iterable[str] = (),
        **opts: Any,
    ) -> None:
        self.name = name
        self.addable = addable
        self.capacity = capacity
        self.stretch = stretch
        self.variable = variable
        self.actions = frozenset(actions)
        self.options: dict[str, Any] = dict(opts)
        self.conf = Conf()
        self._children: list[Placed] = []

    def add(self, component: object, *, at: object | None = None) -> object:
        """放入一个子件；不可增 / 超容量即报错。"""
        if not self.addable:
            raise LayoutError(f"槽不可增: {self.name or self.kind}")
        if self.capacity is not None and len(self._children) >= self.capacity:
            raise LayoutError(f"槽已满（上限 {self.capacity}）: {self.name or self.kind}")
        self._children.append(Placed(component=component, at=at))
        return component

    def children(self) -> list[Placed]:
        """全部子件（按放置顺序）。"""
        return list(self._children)

    def clear(self) -> None:
        """清空子件。"""
        self._children.clear()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, {len(self._children)})"


__all__ = ["Node", "Placed"]
