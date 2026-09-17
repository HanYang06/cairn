# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""类型化视图行（DTO）：跨到界面的数据一律用这些，不用裸 dict。

当前只有笔记行；项目 / 组等后续按同样方式加。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .format import fmt_time

if TYPE_CHECKING:
    from ..domains import Note


@dataclass(frozen=True, slots=True)
class NoteRow:
    """笔记列表/树用的投影：只含展示需要的字段。"""

    oid: str
    title: str
    preview: str
    updated_ms: int
    updated_label: str
    favorite: bool
    archived: bool
    trashed: bool
    tags: tuple[str, ...]

    @classmethod
    def from_note(cls, note: Note) -> NoteRow:
        """从领域笔记投影出一行（属性标志暂读 ``props``，与现有数据兼容）。"""
        props = note.props()
        updated = int(note.info.updated)
        return cls(
            oid=str(note.oid),
            title=note.title or "未命名",
            preview=note.text.strip().replace("\n", " ")[:90],
            updated_ms=updated,
            updated_label=fmt_time(updated),
            favorite=bool(props.get("favorite")),
            archived=bool(props.get("archived")),
            trashed=bool(props.get("trashed")),
            tags=tuple(str(key) for key in note.tags),
        )


@dataclass(frozen=True, slots=True)
class PropertyRow:
    """检查器里的一行属性：``kind`` 决定渲染方式（文本 / 布尔 / 计数）。"""

    pid: str
    key: str
    value: object
    kind: str
    editable: bool


@dataclass(frozen=True, slots=True)
class GroupNode:
    """导航树的节点：组（可嵌套）或笔记（叶子）。"""

    kind: str  # "group" | "note"
    key: str  # 组为 gid（未分组为 ""）；笔记为 oid
    title: str
    children: tuple[GroupNode, ...] = ()


@dataclass(frozen=True, slots=True)
class RelationRow:
    """关系视图的一行：`depth < 0` 上游（来源），`0` 当前，`> 0` 下游（派生）。"""

    oid: str
    title: str
    depth: int
    current: bool


@dataclass(frozen=True, slots=True)
class VersionRow:
    """历史视图的一行。"""

    seq: int
    vid: str
    updated: str
    current: bool


@dataclass(frozen=True, slots=True)
class TabRow:
    """打开标签页的一行：笔记 / 关系 / 历史。"""

    key: str
    title: str
    kind: str


__all__ = [
    "GroupNode",
    "NoteRow",
    "PropertyRow",
    "RelationRow",
    "TabRow",
    "VersionRow",
]
