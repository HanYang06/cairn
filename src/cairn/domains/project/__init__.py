# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""项目领域：继承 ``Block`` 的具名容器，成员通过关系挂载。"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import Any, Self

from ...core.store import Attr, Block, Body
from ...types import Oid
from ..base import UNSET
from ..relation import Relation

PROJECT_KIND = "cairn.project"
PROJECT_SCHEMA = 1
CONTAINS = "contains"


class Project(Block):
    type = PROJECT_KIND
    body = Body(factory=list)

    schema = Attr(default=PROJECT_SCHEMA)

    @classmethod
    def create(
        cls,
        vault: Any,
        name: str,
        *,
        description: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        project = cls()
        project._vault = vault
        project.title = name
        merged = dict(props or {})
        if description is not None:
            merged["description"] = str(description)
        project.attrs["props"] = merged
        project.tags = tags or {}
        project.save()
        return project

    @property
    def name(self) -> str | None:
        return self.title

    @property
    def description(self) -> str | None:
        value = self.props().get("description")
        return None if value is None else str(value)

    def add_member(self, member: Oid | str, *, relation: str = CONTAINS) -> Relation:
        return Relation.create(
            self._require_vault(),
            self.oid,
            member,
            relation=relation,
        )

    def members(self) -> Iterator[Oid]:
        for edge in Relation.outbound(self._require_vault(), self.oid, relation=CONTAINS):
            yield edge.target

    def update(
        self,
        *,
        name: str | None = UNSET,
        description: str | None = UNSET,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        merged = self.props()
        if description is not UNSET:
            if description is None:
                merged.pop("description", None)
            else:
                merged["description"] = str(description)
        if props:
            merged.update(props)
        if name is not UNSET:
            self.title = name
        if tags is not None:
            self.tags = tags
        self.attrs["props"] = merged
        self.save()
        return self


__all__ = ["CONTAINS", "PROJECT_KIND", "PROJECT_SCHEMA", "Project"]
