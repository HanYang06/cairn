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
    SpaceId,
    SpaceNotFoundError,
    VaultError,
    VaultLockedError,
    Visibility,
    now_ms,
)
from .objects import ChunkRef, ObjectInfo, Space

__all__ = [
    "AuthError",
    "CairnError",
    "ChunkRef",
    "Cid",
    "CorruptObjectError",
    "InvalidIdError",
    "ObjectInfo",
    "ObjectNotFoundError",
    "Oid",
    "Space",
    "SpaceId",
    "SpaceNotFoundError",
    "VaultError",
    "VaultLockedError",
    "Visibility",
    "now_ms",
]
