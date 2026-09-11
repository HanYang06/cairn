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

    @classmethod
    def backlinks(
        cls,
        vault: Any,
        target: Oid | str,
        *,
        space: str | SpaceId | None = None,
    ) -> Iterator[Self]:
        wanted = str(target)
        for relation in cls.list(vault, space=space):
            if str(relation.target) == wanted:
                yield relation

    @classmethod
    def outbound(
        cls,
        vault: Any,
        source: Oid | str,
        *,
        space: str | SpaceId | None = None,
    ) -> Iterator[Self]:
        wanted = str(source)
        for relation in cls.list(vault, space=space):
            if str(relation.source) == wanted:
                yield relation
