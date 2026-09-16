# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域层公共：异常与类型登记。

领域结构**直接继承 ``Block``**（不再有中间层）；本模块只放跨领域的异常与登记。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ..core.store import Block
from ..types import CairnError, KindMismatchError

UNSET: Any = object()


def normalize_tags(value: Iterable[str] | Mapping[str, Any]) -> dict[str, str | None]:
    """标签统一成 ``{键: 值}``；纯标签的值为 ``None``（兼容旧的纯列表写法）。"""
    if isinstance(value, Mapping):
        return {str(key): (None if item is None else str(item)) for key, item in value.items()}
    return {str(tag): None for tag in value}


class DomainError(CairnError):
    """领域层错误基类。"""


class UnknownKindError(DomainError):
    """未登记的领域类型。"""


def known_kinds() -> list[str]:
    """已登记的领域类型（块注册表）。"""
    return sorted(Block._REGISTRY)


__all__ = [
    "UNSET",
    "DomainError",
    "KindMismatchError",
    "UnknownKindError",
    "known_kinds",
]
