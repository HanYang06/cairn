"""核心层：本地加密对象池（L0）。

对外只有一套极简门面与动词：Vault 与 ObjectInfo。所有内容都是对象。
"""

from __future__ import annotations

from .types import (
    CairnError,
    CorruptObjectError,
    ObjectInfo,
    ObjectNotFoundError,
    Oid,
    Space,
    SpaceId,
    SpaceNotFoundError,
    VaultError,
    VaultLockedError,
    Visibility,
)
from .vault import Vault

__all__ = [
    "CairnError",
    "CorruptObjectError",
    "ObjectInfo",
    "ObjectNotFoundError",
    "Oid",
    "Space",
    "SpaceId",
    "SpaceNotFoundError",
    "Vault",
    "VaultError",
    "VaultLockedError",
    "Visibility",
]
