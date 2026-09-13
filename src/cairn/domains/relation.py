# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""关系领域：一等、可署名的边。

关系是独立对象（`cairn.relation`），因此第三方可以对你的笔记加边而不改你的对象。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar, Self

from ..core.types import Oid, SpaceId
from .base import DomainObject, get_handler, register

RELATION_KIND = "cairn.relation"
RELATION_SCHEMA = 1


class RelationHandler:
    kind: str = RELATION_KIND
    schema_version: int = RELATION_SCHEMA

    def normalize_meta(self, **fields: Any) -> dict[str, Any]:
        props = dict(fields.get("props") or {})
        props["source"] = str(fields["source"])
        props["target"] = str(fields["target"])
        props["relation"] = str(fields.get("relation", "references"))
        return {
            "title": None,
            "tags": [str(tag) for tag in (fields.get("tags") or ())],
            "schema": RELATION_SCHEMA,
            "props": props,
        }


register(RelationHandler())


class Relation(DomainObject):
    kind: ClassVar[str] = RELATION_KIND

    @classmethod
    def create(
        cls,
        vault: Any,
        source: Oid | str,
        target: Oid | str,
        relation: str = "references",
        *,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
        space: str | SpaceId = "default",
    ) -> Self:
        meta = get_handler(cls.kind).normalize_meta(
            source=source, target=target, relation=relation, tags=tags, props=props
        )
        oid = vault.put(b"", space=space, type=cls.kind, meta=meta)
        return cls.load(vault, oid)

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
        """该边所钉的被派生版本（fork 时的源 seq/哈希）；无则 None。"""
        value = self.props().get("at")
        return None if value is None else str(value)

    @classmethod
    def backlinks(
        cls,
        vault: Any,
        target: Oid | str,
        *,
        relation: str | None = None,
        space: str | SpaceId | None = None,
    ) -> Iterator[Self]:
        wanted = str(target)
        for item in cls.list(vault, space=space):
            if str(item.target) == wanted and (relation is None or item.relation == relation):
                yield item

    @classmethod
    def outbound(
        cls,
        vault: Any,
        source: Oid | str,
        *,
        relation: str | None = None,
        space: str | SpaceId | None = None,
    ) -> Iterator[Self]:
        wanted = str(source)
        for item in cls.list(vault, space=space):
            if str(item.source) == wanted and (relation is None or item.relation == relation):
                yield item
