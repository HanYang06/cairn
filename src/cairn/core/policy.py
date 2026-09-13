# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""分享策略：把「分享给谁 / 哪里」映射为可传播的受众。

对象默认私密。分享目标是**列表**（不互斥），例如「个人主页 + 某社区 + 某人」。
个人离线模式无需判断；P2P / 社区架构下由网络层调用这里的判定。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from enum import Enum


class Audience(Enum):
    """接收方类别。"""

    SELF = "self"
    PEER = "peer"
    COMMUNITY = "community"
    PUBLIC = "public"


class ShareKind(Enum):
    """分享目标的类型。"""

    HOMEPAGE = "homepage"  # 挂到个人主页 → 公开
    COMMUNITY = "community"  # 发到某社区
    PERSON = "person"  # 直发给某人


_RANK: dict[Audience, int] = {
    Audience.SELF: 0,
    Audience.PEER: 1,
    Audience.COMMUNITY: 2,
    Audience.PUBLIC: 3,
}
_TARGET: dict[ShareKind, Audience] = {
    ShareKind.HOMEPAGE: Audience.PUBLIC,
    ShareKind.COMMUNITY: Audience.COMMUNITY,
    ShareKind.PERSON: Audience.PEER,
}


def parse_kind(value: object) -> ShareKind | None:
    try:
        return ShareKind(str(value))
    except ValueError:
        return None


def target_audience(kind: ShareKind) -> Audience:
    return _TARGET[kind]


def is_private(shares: Iterable[Mapping[str, object]]) -> bool:
    """没有任何分享目标即私密（仅自己可见）。"""
    return not list(shares)


def visible_to(shares: Iterable[Mapping[str, object]], audience: Audience) -> bool:
    """对象对该类受众是否可见（粗略：按目标的受众层级传递）。"""
    if audience is Audience.SELF:
        return True
    limit = _RANK[audience]
    for entry in shares:
        kind = parse_kind(entry.get("kind"))
        if kind is not None and _RANK[_TARGET[kind]] >= limit:
            return True
    return False


__all__ = [
    "Audience",
    "ShareKind",
    "is_private",
    "parse_kind",
    "target_audience",
    "visible_to",
]
