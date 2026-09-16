# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记衍生关系：沿"派生"关系遍历来源与派生。

约定：``derived-from`` 边的方向为 **派生者 → 被派生者**（source 派生自 target）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .relation import Relation

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ..core.types import Oid

DERIVED_FROM = "derived-from"


def derivatives(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
) -> Iterator[Relation]:
    """直接派生自 ``oid`` 的关系（谁基于它改的）。"""
    return Relation.backlinks(vault, oid, relation=relation)


def lineage(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
) -> Iterator[Relation]:
    """``oid`` 直接派生自谁。"""
    return Relation.outbound(vault, oid, relation=relation)


def descendants(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
) -> tuple[Oid, ...]:
    """所有（递归）派生自 ``oid`` 的对象。"""
    seen: set[str] = set()
    order: list[Oid] = []
    frontier = [str(oid)]
    while frontier:
        current = frontier.pop(0)
        for edge in Relation.backlinks(vault, current, relation=relation):
            child = str(edge.source)
            if child not in seen:
                seen.add(child)
                order.append(edge.source)
                frontier.append(child)
    return tuple(order)


def ancestors(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
) -> tuple[Oid, ...]:
    """``oid`` 的（递归）来源对象。"""
    seen: set[str] = set()
    order: list[Oid] = []
    frontier = [str(oid)]
    while frontier:
        current = frontier.pop(0)
        for edge in Relation.outbound(vault, current, relation=relation):
            parent = str(edge.target)
            if parent not in seen:
                seen.add(parent)
                order.append(edge.target)
                frontier.append(parent)
    return tuple(order)
