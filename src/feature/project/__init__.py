# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""项目领域：**数据**（``ProjectData``）与**域服务**（``Project``）分离。

- ``ProjectData(Block)``：具名容器数据 + 属性。
- ``Project(Domain)``：域服务——创建 / 载入 / 更新 / 成员关系（``contains``）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.signal import Domain, action
from core.storage import Attr, Block, BodyField

from ..shared.base import UNSET, normalize_tags
from ..shared.kinds import Kind
from ..shared.relation import Relation

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from core.types import Oid

PROJECT_KIND = Kind.Data.Projectdata
PROJECT_SCHEMA = 1
CONTAINS = "contains"


class ProjectData(Block):
    """项目数据块：承载一组条目（``contains`` 关系）。"""

    type = PROJECT_KIND
    body = BodyField(factory=list)

    schema: Attr[int] = PROJECT_SCHEMA
    title: Attr[str | None] = None
    tags: Attr = Attr(factory=dict, coerce=normalize_tags)

    @property
    def name(self) -> str | None:
        return self.title

    @property
    def description(self) -> str | None:
        value = self.props().get("description")
        return None if value is None else str(value)


class Project(Domain):
    """项目域服务（单例）：创建 / 载入 / 更新 / 成员关系。"""

    type = Kind.Feature.Project
    data = (ProjectData,)  # 本域用到的数据类
    light = [ProjectData]  # noqa: RUF012 — 最小数据单元（可多个）

    def __init__(self, vault: Any) -> None:
        self.vault = vault

    @action
    def create(
        self,
        name: str,
        *,
        description: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> ProjectData:
        """新建项目并落盘。"""
        data = ProjectData()
        data._vault = self.vault  # noqa: SLF001 — 服务为数据绑定库
        data.title = name
        merged = dict(props or {})
        if description is not None:
            merged["description"] = str(description)
        data.attrs["props"] = merged
        data.tags = tags or {}
        data.save()
        return data

    @action
    def load(self, oid: Oid | str) -> ProjectData:
        """按 oid 载入项目数据。"""
        data: ProjectData = ProjectData.load(self.vault, oid)
        return data

    @action
    def update(
        self,
        data: ProjectData,
        *,
        name: str | None = UNSET,
        description: str | None = UNSET,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> ProjectData:
        """更新项目属性并落盘。"""
        merged = data.props()
        if description is not UNSET:
            if description is None:
                merged.pop("description", None)
            else:
                merged["description"] = str(description)
        if props:
            merged.update(props)
        if name is not UNSET:
            data.title = name
        if tags is not None:
            data.tags = tags
        data.attrs["props"] = merged
        data.save()
        return data

    @action
    def add_member(
        self,
        data: ProjectData,
        member: Oid | str,
        *,
        relation: str = CONTAINS,
    ) -> Relation:
        """把一个对象加为项目成员（建 ``contains`` 边）。"""
        return Relation.create(self.vault, data.oid, member, relation=relation, domain="project")

    @action
    def members(self, data: ProjectData) -> list[Oid]:
        """项目成员（``contains`` 边的目标）。"""
        return [edge.target for edge in Relation.outbound(self.vault, data.oid, relation=CONTAINS)]


__all__ = ["CONTAINS", "PROJECT_KIND", "PROJECT_SCHEMA", "Project", "ProjectData"]
