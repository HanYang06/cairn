# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""关系领域：继承 ``Block`` 的边（可署名、可加属性）。"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Self

from ..core.store import Attr, Block, Body
from ..types import Oid

RELATION_KIND = "cairn.relation"
RELATION_SCHEMA = 1


class Relation(Block):
    type = RELATION_KIND
    body = Body(factory=list)

    schema = Attr(default=RELATION_SCHEMA)

    @classmethod
    def create(
        cls,
        vault: Any,
        source: Oid | str,
        target: Oid | str,
        relation: str = "references",
        *,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
        space: Any = None,
    ) -> Self:
        del space
        edge = cls()
        edge._vault = vault
        merged = dict(props or {})
        merged.update(
            {
                "source": str(source),
                "target": str(target),
                "relation": str(relation),
            }
        )
        edge.attrs["props"] = merged
        edge.tags = tags or {}
        edge.save()
        return edge

    @property
    def source(self) -> Oid:
        return Oid.parse(str(self.props()["source"]))

    @property
    def target(self) -> Oid:
        return Oid.parse(str(self.props()["target"]))

    @property
    def relation(self) -> str:
        return str(self.props().get("relation", "references"))

    @property
    def at(self) -> str | None:
        """该边所钉的被派生版本；无则 None。"""
        value = self.props().get("at")
        return None if value is None else str(value)

    @classmethod
    def backlinks(
        cls,
        vault: Any,
        target: Oid | str,
        *,
        relation: str | None = None,
        space: Any = None,
    ) -> Iterator[Self]:
        del space
        wanted = str(target)
        for item in cls.list(vault):
            if str(item.target) == wanted and (relation is None or item.relation == relation):
                yield item

    @classmethod
    def outbound(
        cls,
        vault: Any,
        source: Oid | str,
        *,
        relation: str | None = None,
        space: Any = None,
    ) -> Iterator[Self]:
        del space
        wanted = str(source)
        for item in cls.list(vault):
            if str(item.source) == wanted and (relation is None or item.relation == relation):
                yield item


__all__ = ["RELATION_KIND", "RELATION_SCHEMA", "Relation"]
