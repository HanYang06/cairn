# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域层公共：异常与类型登记。

领域结构**直接继承 ``Block``**（不再有中间层）；本模块只放跨领域的异常与登记。
"""

from __future__ import annotations

from typing import Any

from ..core.store import Block
from ..types import CairnError, KindMismatchError

UNSET: Any = object()


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
