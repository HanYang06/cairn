"""组装领域：文档 / 博客 = 对其它节点的排布（transclusion）。"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Self

from ..core.types import Oid, SpaceId
from .base import DomainObject, get_handler, register

COMPOSITION_KIND = "cairn.composition"
COMPOSITION_SCHEMA = 1


class CompositionHandler:
    kind: str = COMPOSITION_KIND
    schema_version: int = COMPOSITION_SCHEMA

    def normalize_meta(self, **fields: Any) -> dict[str, Any]:
        props = dict(fields.get("props") or {})
        props["items"] = [str(item) for item in (fields.get("items") or ())]
        title = fields.get("title")
        return {
            "title": None if title is None else str(title),
            "tags": [str(tag) for tag in (fields.get("tags") or ())],
            "schema": COMPOSITION_SCHEMA,
            "props": props,
        }


register(CompositionHandler())


class Composition(DomainObject):
    kind: ClassVar[str] = COMPOSITION_KIND

    @classmethod
    def create(
        cls,
        vault: Any,
        items: Iterable[Oid | str] = (),
        *,
        title: str | None = None,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
        space: str | SpaceId = "default",
    ) -> Self:
        meta = get_handler(cls.kind).normalize_meta(
            items=items, title=title, tags=tags, props=props
        )
        oid = vault.put(b"", space=space, type=cls.kind, meta=meta)
        return cls.load(vault, oid)

    @property
    def items(self) -> tuple[Oid, ...]:
        return tuple(Oid.parse(str(item)) for item in (self.props().get("items") or ()))
