# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核数据结构：对象层结构。

基础数据结构（标识符 / 枚举 / 错误 / 通用）见 ``cairn.types``。
此处重导出基础类型以保持既有导入可用。
"""

from __future__ import annotations

from ...types import (
    AuthError,
    CairnError,
    Cid,
    CorruptObjectError,
    InvalidIdError,
    ObjectNotFoundError,
    Oid,
    VaultError,
    now_ms,
)
from .objects import ObjectInfo, VerifyReport, VersionInfo

__all__ = [
    "AuthError",
    "CairnError",
    "Cid",
    "CorruptObjectError",
    "InvalidIdError",
    "ObjectInfo",
    "ObjectNotFoundError",
    "Oid",
    "VaultError",
    "VerifyReport",
    "VersionInfo",
    "now_ms",
]
