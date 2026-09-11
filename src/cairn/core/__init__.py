"""核心层：本地加密对象池（L0）。

对外只有一套极简门面与动词：Vault 与 ObjectInfo。所有内容都是对象。
"""

from __future__ import annotations

from .events import (
    Event,
    ObjectDeleted,
    ObjectPut,
    SpaceCreated,
    Subscription,
    VaultLocked,
    VaultUnlocked,
)
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
    "Event",
    "ObjectDeleted",
    "ObjectInfo",
    "ObjectNotFoundError",
    "ObjectPut",
    "Oid",
    "Space",
    "SpaceCreated",
    "SpaceId",
    "SpaceNotFoundError",
    "Subscription",
    "Vault",
    "VaultError",
    "VaultLocked",
    "VaultLockedError",
    "VaultUnlocked",
    "Visibility",
]
