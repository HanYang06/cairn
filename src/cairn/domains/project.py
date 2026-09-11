"""项目领域：一个具名容器，成员通过关系挂载。

项目本身也是对象；"包含哪些对象"由 ``contains`` 关系表达，而非塞进结构。
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar, Self

from ..core.types import Oid, SpaceId
from .base import UNSET, DomainObject, get_handler, register
from .relation import Relation

PROJECT_KIND = "cairn.project"
PROJECT_SCHEMA = 1
CONTAINS = "contains"


class ProjectHandler:
    kind: str = PROJECT_KIND
    schema_version: int = PROJECT_SCHEMA

    def normalize_meta(self, **fields: Any) -> dict[str, Any]:
        props = dict(fields.get("props") or {})
        description = fields.get("description")
        if description is not None:
            props["description"] = str(description)
        name = fields.get("name")
        return {
            "title": None if name is None else str(name),
            "tags": [str(tag) for tag in (fields.get("tags") or ())],
            "schema": PROJECT_SCHEMA,
            "props": props,
        }


register(ProjectHandler())


class Project(DomainObject):
    kind: ClassVar[str] = PROJECT_KIND
    schema_version: ClassVar[int] = PROJECT_SCHEMA

    @classmethod
    def create(
        cls,
        vault: Any,
        name: str,
        *,
        description: str | None = None,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
        space: str | SpaceId = "default",
    ) -> Self:
        meta = get_handler(cls.kind).normalize_meta(
            name=name, description=description, tags=tags, props=props
        )
        oid = vault.put(b"", space=space, type=cls.kind, meta=meta)
        return cls.load(vault, oid)

    @property
    def name(self) -> str | None:
        return self.title

    @property
    def description(self) -> str | None:
        return self.props().get("description")

    def add_member(self, member: Oid | str, *, relation: str = CONTAINS) -> Relation:
        return Relation.create(
            self._vault,
            self._oid,
            member,
            relation=relation,
            space=self._info.space_id,
        )

    def members(self) -> Iterator[Oid]:
        for edge in Relation.outbound(self._vault, self._oid, relation=CONTAINS):
            yield edge.target

    def update(
        self,
        *,
        name: str | None = UNSET,
        description: str | None = UNSET,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        current = self.meta()
        merged_props = dict(current.get("props") or {})
        if description is not UNSET:
            if description is None:
                merged_props.pop("description", None)
            else:
                merged_props["description"] = str(description)
        if props:
            merged_props.update(props)
        new_name = current.get("title") if name is UNSET else name
        new_tags = list(current.get("tags") or ()) if tags is None else list(tags)
        meta = get_handler(self.kind).normalize_meta(
            name=new_name,
            description=merged_props.get("description"),
            tags=new_tags,
            props=merged_props,
        )
        self._put(b"", meta=meta)
        self._refresh()
        return self
