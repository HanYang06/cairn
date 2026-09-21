# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""类型层：基础数据结构 + 内核对象层结构。

基础（标识符 / 错误 / 通用）与对象层视图（元数据 / 巡检）同处一层，
对外只暴露 ``core.types``。
"""

from __future__ import annotations

from .attr import Attr, Data
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
from .kind import (
    ROLE_DATA,
    ROLE_DOMAIN,
    TypeInfo,
    collect_fields,
    domain_of,
    register,
    type_info,
    type_name,
    types,
    unit_infos,
)
from .objects import ObjectInfo, VerifyReport

__all__ = [
    "ROLE_DATA",
    "ROLE_DOMAIN",
    "Attr",
    "AuthError",
    "CairnError",
    "Cid",
    "CorruptObjectError",
    "Data",
    "InvalidIdError",
    "KindMismatchError",
    "ObjectInfo",
    "ObjectNotFoundError",
    "Oid",
    "TypeInfo",
    "VaultError",
    "VerifyReport",
    "collect_fields",
    "domain_of",
    "now_ms",
    "register",
    "type_info",
    "type_name",
    "types",
    "unit_infos",
]
