# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""声明节点：UI 描述树的通用基元与注册表。

一个节点 = 名称 + 配置 + 子件 + **能力声明** + **词汇元数据**（`STYLABLE` / `STATES`）。
布局、组件、页面都是它的子类；子类按 `kind` 自动登记，供配置 schema 与编译查表。

这是 UI 内核的底座：**新形态只需声明 `kind` + 元数据**，其余机制（配置、编译、绑定）通用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from .conf import Conf
from .errors import LayoutError

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


@dataclass(frozen=True)
class Placed:
    """一个放置结果：子件 + 位置（有格 / 序的布局才用）。"""

    component: object
    at: object | None = None


class Node:
    """声明节点基类。"""

    kind: ClassVar[str] = "node"

    # 词汇元数据：可样式化属性 + 可表达状态（供主题 schema 与校验）
    STYLABLE: ClassVar[frozenset[str]] = frozenset()
    STATES: ClassVar[frozenset[str]] = frozenset()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        kind = cls.__dict__.get("kind")
        if not kind:
            return
        existing = _KINDS.get(kind)
        if existing is not None and existing is not cls:
            raise LayoutError(f"节点类型冲突: {kind!r} 已由 {existing.__name__} 登记")
        _KINDS[kind] = cls

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
        self._parent: Node | None = None
        self._widget: object | None = None

    # ---- 目标控件（编译期回填，供信号连接）----
    def bind_widget(self, widget: object) -> None:
        """编译期回填本节点对应的目标控件。"""
        self._widget = widget

    @property
    def widget(self) -> object | None:
        """本节点对应的目标控件（未编译为 `None`）。"""
        return self._widget

    # ---- 父子 / 路径 ----
    @property
    def parent(self) -> Node | None:
        """父节点（根为 `None`）。"""
        return self._parent

    def path(self, *, root: str = "app") -> str:
        """从根到本节点的点分路径（节点无名字时退化为 `kind`）。"""
        parts: list[str] = []
        node: Node | None = self
        while node is not None:
            parts.append(node.name or node.kind)
            node = node._parent  # noqa: SLF001 — 树查链，同模块强耦合
        parts.reverse()
        return ".".join([root, *parts])

    def walk(self) -> Iterator[Node]:
        """深度优先遍历自身与全部子孙。"""
        yield self
        for placed in self._children:
            if isinstance(placed.component, Node):
                yield from placed.component.walk()

    # ---- 子件 ----
    def add(self, component: object, *, at: object | None = None) -> object:
        """放入一个子件；不可增 / 超容量即报错。"""
        if not self.addable:
            raise LayoutError(f"槽不可增: {self.name or self.kind}")
        if self.capacity is not None and len(self._children) >= self.capacity:
            raise LayoutError(f"槽已满（上限 {self.capacity}）: {self.name or self.kind}")
        if isinstance(component, Node):
            component._parent = self  # noqa: SLF001 — 建树，同模块强耦合
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


# 节点类型注册表（在 Node 定义后建立；`__init_subclass__` 运行期引用）。
_KINDS: dict[str, type[Node]] = {}


def registered_kinds() -> dict[str, type[Node]]:
    """已登记的节点类型：`kind → 类`。"""
    return dict(_KINDS)


__all__ = ["Node", "Placed", "registered_kinds"]
