# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""核心层：本地内容寻址的桶 / 块存储（L0）。

对外只有一套极简门面与动词：Vault 与 ObjectInfo。所有内容都是块。
"""

from __future__ import annotations

from .policy import Audience, ShareKind, is_private, target_audience, visible_to
from .signal import (
    Event,
    ObjectDeleted,
    ObjectPut,
    Subscription,
)
from .types import (
    CairnError,
    CorruptObjectError,
    ObjectInfo,
    ObjectNotFoundError,
    Oid,
    VaultError,
)
from .vault import Vault

__all__ = [
    "Audience",
    "CairnError",
    "CorruptObjectError",
    "Event",
    "ObjectDeleted",
    "ObjectInfo",
    "ObjectNotFoundError",
    "ObjectPut",
    "Oid",
    "ShareKind",
    "Subscription",
    "Vault",
    "VaultError",
    "is_private",
    "target_audience",
    "visible_to",
]
