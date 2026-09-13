# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""可见性策略：某可见性档位的对象能否传给某类受众。

个人离线模式无需判断；P2P / 社区架构下由网络层调用。
这里只固化「档位 → 允许的受众集合」这一简单规则。
"""

from __future__ import annotations

from enum import Enum

from .types import Visibility


class Audience(Enum):
    """接收方类别。"""

    SELF = "self"
    PEER = "peer"
    COMMUNITY = "community"
    PUBLIC = "public"


_ALLOWED: dict[Visibility, frozenset[Audience]] = {
    Visibility.PRIVATE: frozenset({Audience.SELF}),
    Visibility.DIRECT: frozenset({Audience.SELF, Audience.PEER}),
    Visibility.COMMUNAL: frozenset({Audience.SELF, Audience.PEER, Audience.COMMUNITY}),
    Visibility.PUBLIC: frozenset(
        {Audience.SELF, Audience.PEER, Audience.COMMUNITY, Audience.PUBLIC}
    ),
}


def can_share(visibility: Visibility, audience: Audience) -> bool:
    """该可见性的对象是否可传给该类受众。"""
    return audience in _ALLOWED.get(visibility, frozenset({Audience.SELF}))


__all__ = ["Audience", "can_share"]
