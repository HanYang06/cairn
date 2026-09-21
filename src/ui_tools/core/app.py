# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核 · 组合根（`App`）。

`App` 是根：它持一块**大方框** `root`，App 作者用通用格子（布局 / 组件 / 槽）把它组织成
任意结构（三栏、异形、随便）；再 `add(facet)` 把领域组织器挂上来，按槽的 `expects`
自动把 `facet.parts()` 的同名部件填进对应槽。

工具里**没有任何业务词汇**（没有 topbar / navigator / content）——名字都是 App 自己起的。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .bind import Bind
from .errors import LayoutError, UiError
from .node import Node
from .schema import Schema
from .slot import Slot
from .theme import Theme

if TYPE_CHECKING:
    from .facet import Facet
    from .session import Session


class App:
    """根：大方框 + 绑定 + 主题。"""

    def __init__(self, session: Session, *, theme: Theme | None = None) -> None:
        self.session = session
        self.theme = theme or Theme()
        self.root = Node("app")
        self.bind = Bind()
        self._facets: list[Facet] = []

    def slots(self) -> list[Slot]:
        """根结构里的全部槽位（有序）。"""
        return [node for node in self.root.walk() if isinstance(node, Slot)]

    def add(self, facet: Facet) -> Facet:
        """挂一个组织器：按槽的 `expects` 取 `parts()` 同名部件填入。

        先整体校验（重复 expects / 槽不可增 / 容量），再统一写入——避免挂到一半失败。
        """
        if facet in self._facets:
            return facet
        parts = facet.parts()
        targets: list[tuple[Slot, object]] = []
        used: set[str] = set()
        for slot in self.slots():
            if slot.expects is None or slot.expects not in parts:
                continue
            if slot.expects in used:
                raise UiError(f"多个槽期待同一部件: {slot.expects!r}")
            if not slot.addable:
                raise LayoutError(f"槽不可增: {slot.name or slot.kind}")
            if slot.capacity is not None and len(slot.children()) >= slot.capacity:
                raise LayoutError(f"槽已满（上限 {slot.capacity}）: {slot.name or slot.kind}")
            used.add(slot.expects)
            targets.append((slot, parts[slot.expects]))
        for slot, part in targets:
            slot.add(part)
        self._facets.append(facet)
        return facet

    def facets(self) -> list[Facet]:
        """已挂载的组织器。"""
        return list(self._facets)

    def schema(self) -> Schema:
        """由已挂载 Facet 编译配置路径树（含路径 → 节点）。"""
        schema = Schema()
        for facet in self._facets:
            for rel, node in facet.node_paths():
                schema.add(f"app.{rel}", node)
        return schema


__all__ = ["App"]
