# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""官方领域类型词表（`StrEnum`）：**值是持久化字符串**，枚举只做编译期安全。

- 官方类型一律用枚举比较，别再裸写字符串；`Kind.NOTE == "cairn.note"` 恒真。
- 第三方类型仍可用自有前缀字符串（开放世界）；类型表按 `str()` 归一，两者可互换。
"""

from __future__ import annotations

from enum import StrEnum


class Kind(StrEnum):
    """官方领域类型（`cairn.*`）。"""

    NOTE = "cairn.note"
    PROJECT = "cairn.project"
    CANVAS = "cairn.canvas"
    ASSET = "cairn.asset"
    GROUP = "cairn.group"


__all__ = ["Kind"]
