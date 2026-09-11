"""笔记族谱：沿"派生"关系遍历来源与派生。

约定：``derived-from`` 边的方向为 **派生者 → 被派生者**（source 派生自 target）。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..core.types import Oid, SpaceId
from .relation import Relation

DERIVED_FROM = "derived-from"


def derivatives(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
    space: str | SpaceId | None = None,
) -> Iterator[Relation]:
    """直接派生自 ``oid`` 的关系（谁基于它改的）。"""
    return Relation.backlinks(vault, oid, relation=relation, space=space)


def lineage(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
    space: str | SpaceId | None = None,
) -> Iterator[Relation]:
    """``oid`` 直接派生自谁。"""
    return Relation.outbound(vault, oid, relation=relation, space=space)


def descendants(
    vault: Any,
    oid: Oid | str,
    *,
    relation: str = DERIVED_FROM,
    space: str | SpaceId | None = None,
) -> tuple[Oid, ...]:
    """所有（递归）派生自 ``oid`` 的对象。"""
    seen: set[str] = set()
    order: list[Oid] = []
    frontier = [str(oid)]
    while frontier:
        current = frontier.pop(0)
        for edge in Relation.backlinks(vault, current, relation=relation, space=space):
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
    space: str | SpaceId | None = None,
) -> tuple[Oid, ...]:
    """``oid`` 的（递归）来源对象。"""
    seen: set[str] = set()
    order: list[Oid] = []
    frontier = [str(oid)]
    while frontier:
        current = frontier.pop(0)
        for edge in Relation.outbound(vault, current, relation=relation, space=space):
            parent = str(edge.target)
            if parent not in seen:
                seen.add(parent)
                order.append(edge.target)
                frontier.append(parent)
    return tuple(order)
