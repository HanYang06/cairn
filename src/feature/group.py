# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组（Group）：管理一组 ID 的容器，可无限嵌套。

- **组是块**（``cairn.group``）：有自己的稳定域 ID ``gid``，与块的存储身份 ``oid`` **分开**。
- ``group``：有序子项列表，装笔记 / 项目 / 组的 ID（组存 ``gid``，其余存 ``oid``），顺序即显示顺序。
- ``lock``：锁定后不可再增删成员。
- ``owner`` / ``member``：社区化的「有限编辑组」预埋；``User`` 系统落地前暂用字符串。
- ``key``：访问口令（非空则进组要密码，密码本身不是加密）。
- 成员关系**两套都存**：``group`` 列表存结构（顺序），``relations`` 表存 ``contains`` 关系（反查）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from core.storage import Attr, Block, BodyField
from core.types import Oid

from .base import DomainError
from .relation import CONTAINS as _CONTAINS
from .relation import Relation

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

GROUP_KIND = "cairn.group"
GROUP_MIME = "application/x-cairn-group"
GROUP_SCHEMA = 1


class GroupError(DomainError):
    """组操作非法（如锁定后编辑）。"""


class Group(Block):
    """组块：``gid`` 为域身份，``group`` 为有序子项 ID 列表。"""

    type = GROUP_KIND
    mime: ClassVar[str | None] = GROUP_MIME
    body = BodyField()

    schema: Attr[int] = GROUP_SCHEMA
    gid: Attr[str] = ""
    title: Attr[str] = ""
    lock: Attr[bool] = False
    owner: Attr[str] = ""
    key: Attr[str] = ""
    group: list[str] = []  # noqa: RUF012  # 有序子项 ID 列表（结构）
    member: list[str] = []  # noqa: RUF012  # 预留：社区成员（User 系统落地后换类型）

    def _require_unlocked(self) -> None:
        if self.lock:
            raise GroupError(f"组已锁定，不可编辑: {self.gid or self.id}")

    @staticmethod
    def ref_of(child: Block | str) -> str:
        """子项在 ``group`` 列表里的 ID：组存 ``gid``，其余存块 ``oid``。"""
        if isinstance(child, Group):
            return child.gid or str(child.oid)
        if isinstance(child, Block):
            return str(child.oid)
        return str(child)

    @classmethod
    def create(  # noqa: PLR0913 — 建组入口：描述字段均有默认值
        cls,
        vault: Any,
        title: str = "",
        *,
        parent: Group | None = None,
        key: str = "",
        owner: str = "",
        member: Iterable[str] | None = None,
    ) -> Self:
        group = cls()
        group._vault = vault
        group.gid = str(Oid.new())
        group.title = title
        group.key = key
        group.owner = owner
        group.member = [str(item) for item in member or ()]
        group.save()
        if parent is not None:
            parent.add(group)
        return group

    # ---- 子项 ----
    def add(self, child: Block | str) -> Group:
        """把笔记 / 项目 / 组加进本组（去重、保序），并落一条 ``contains`` 关系。"""
        self._require_unlocked()
        ref = self.ref_of(child)
        if ref and ref not in self.group:
            self.group = [*self.group, ref]
            self._link_relation(child)
            self.save()
        return self

    def remove(self, child: Block | str) -> Group:
        """从本组移除子项（只摘列表；关系行留给后续清理策略）。"""
        self._require_unlocked()
        self.group = [ref for ref in self.group if ref != self.ref_of(child)]
        self.save()
        return self

    def move(self, order: Sequence[int]) -> Group:
        """按旧下标重排子项。"""
        self._require_unlocked()
        items = list(self.group)
        self.group = [items[index] for index in order]
        self.save()
        return self

    def _link_relation(self, child: Block | str) -> None:
        if self._vault is None:
            return
        target = str(child.oid) if isinstance(child, Block) else str(child)
        Relation.create(self._vault, self.oid, target, relation=_CONTAINS)

    def subgroups(self, vault: Any) -> list[Group]:
        """按 ``gid`` 解析出子组（引用不到的忽略），保持列表顺序。"""
        index = {group.gid: group for group in Group.list(vault)}
        return [index[ref] for ref in self.group if ref in index]

    @classmethod
    def by_gid(cls, vault: Any, gid: str) -> Group | None:
        """按域 ID 找组。"""
        for group in cls.list(vault):
            if group.gid == gid:
                return group
        return None


def list_groups(vault: Any) -> Iterator[Group]:
    """列出全部组。"""
    return Group.list(vault)


def all_gids(vault: Any) -> set[str]:
    """全部组的 ``gid`` 集合（判定子项是组还是普通块）。"""
    return {group.gid for group in Group.list(vault)}


def roots(vault: Any) -> list[Group]:
    """没有被任何组包含的组。"""
    groups = list(Group.list(vault))
    contained: set[str] = set()
    for group in groups:
        contained.update(group.group)
    return [group for group in groups if group.gid not in contained]


__all__ = [
    "GROUP_KIND",
    "GROUP_MIME",
    "GROUP_SCHEMA",
    "Group",
    "GroupError",
    "all_gids",
    "list_groups",
    "roots",
]
