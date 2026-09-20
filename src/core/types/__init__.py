# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""类型层：基础数据结构 + 内核对象层结构。

基础（标识符 / 错误 / 通用）与对象层视图（元数据 / 巡检）同处一层，
对外只暴露 ``core.types``。
"""

from __future__ import annotations

from .common import now_ms
from .errors import (
    AuthError,
    CairnError,
    CorruptObjectError,
    InvalidIdError,
    KindMismatchError,
    ObjectNotFoundError,
    VaultError,
)
from .ids import Cid, Oid
from .objects import ObjectInfo, VerifyReport

__all__ = [
    "AuthError",
    "CairnError",
    "Cid",
    "CorruptObjectError",
    "InvalidIdError",
    "KindMismatchError",
    "ObjectInfo",
    "ObjectNotFoundError",
    "Oid",
    "VaultError",
    "VerifyReport",
    "now_ms",
]
