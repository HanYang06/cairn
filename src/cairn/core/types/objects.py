# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核数据结构：对象层结构（元数据视图、版本视图、巡检报告）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...types import Oid


@dataclass(frozen=True, slots=True)
class ObjectInfo:
    """对象的元数据视图，不含其内容。"""

    oid: Oid
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
class VerifyReport:
    """完整性巡检结果。``problems`` 为空表示健康。"""

    objects: int
    problems: tuple[str, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.problems


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """对象的一个历史版本视图（域版本策略填充）。"""

    seq: int
    updated: int
    size: int
    is_current: bool = False
    author: str = ""
