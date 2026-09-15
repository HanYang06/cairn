# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核数据结构：对象层结构（清单引用、元数据视图、空间）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...types import Cid, Oid, SpaceId, Visibility


@dataclass(frozen=True, slots=True)
class ChunkRef:
    """清单中对一个块的引用。"""

    cid: Cid
    size: int


@dataclass(frozen=True, slots=True)
class ObjectInfo:
    """对象的元数据视图，不含其内容。"""

    oid: Oid
    space_id: SpaceId
    type: str
    mime: str | None
    size: int
    created: int
    updated: int
    title: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)
    seq: int = 0
    author: str = ""


@dataclass(frozen=True, slots=True)
class Space:
    """空间：策略与密钥的载体。"""

    space_id: SpaceId
    name: str
    visibility: Visibility
    created: int


@dataclass(frozen=True, slots=True)
class VerifyReport:
    """完整性巡检结果。``problems`` 为空表示健康。"""

    objects: int
    chunks: int
    problems: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.problems


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """对象的一个历史版本（由 manifest.prev 归档链派生）。"""

    seq: int
    updated: int
    size: int
    is_current: bool = False
    author: str = ""
