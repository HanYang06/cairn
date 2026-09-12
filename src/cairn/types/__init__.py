# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""基础数据结构（跨层共享）：标识符、枚举、错误、通用工具。"""

from __future__ import annotations

from .common import now_ms
from .enums import Visibility
from .errors import (
    AuthError,
    CairnError,
    CorruptObjectError,
    InvalidIdError,
    ObjectNotFoundError,
    SpaceNotFoundError,
    VaultError,
    VaultLockedError,
)
from .ids import Cid, Oid, SpaceId

__all__ = [
    "AuthError",
    "CairnError",
    "Cid",
    "CorruptObjectError",
    "InvalidIdError",
    "ObjectNotFoundError",
    "Oid",
    "SpaceId",
    "SpaceNotFoundError",
    "VaultError",
    "VaultLockedError",
    "Visibility",
    "now_ms",
]
