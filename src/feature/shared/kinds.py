# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""类型词表：`Kind.Feature`（领域）/ `Kind.Data`（数据）。

- **Feature**：领域类型（管理型、单例、不落盘），如 `Kind.Feature.Note`。
- **Data**：数据类型（落盘的块类型），如 `Kind.Data.Notedata`；`Block.type` 取它的值。
- 第三方类型仍可用自有前缀字符串（开放世界）；类型表按值归一，两者可互换。
"""

from __future__ import annotations

from enum import Enum


class Kind:
    """类型词表（命名空间，不实例化）。"""

    class Feature(Enum):
        """领域类型。"""

        Note = "note"
        Project = "project"

    class Data(Enum):
        """数据类型（块类型）。"""

        Notedata = "notedata"
        Projectdata = "projectdata"
        Canvas = "canvas"
        Asset = "asset"
        Group = "group"


__all__ = ["Kind"]
