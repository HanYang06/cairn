# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""存储层：桶 + 块。

    Bucket  载体——受管的文件系统，**类**，不是数据结构
    Block   存储单元——``{id, checksum, type, body, attrs}``

其余一切（笔记 / 项目 / 多媒体 / 索引 / 变更）都是块的一种 ``type`` / ``body``。

> 字段标注（``Attr`` / ``Data``）**不在这里**：它们是**声明**，见 `core.types.attr`。
> 存储只负责"放得进、取得出、找得到"，标注不属于它。
"""

from __future__ import annotations

from .block import (
    BLOCK_VERSION,
    INDEX_TYPE,
    PART_TYPE,
    Block,
    Body,
    BodyField,
    canonical,
    decode_canonical,
)
from .bucket import CATALOG_NAME, Bucket, BucketConfig
from .catalog import BlockLocation, Catalog
from .engine import Storage
from .table import Table

__all__ = [
    "BLOCK_VERSION",
    "CATALOG_NAME",
    "INDEX_TYPE",
    "PART_TYPE",
    "Block",
    "BlockLocation",
    "Body",
    "BodyField",
    "Bucket",
    "BucketConfig",
    "Catalog",
    "Storage",
    "Table",
    "canonical",
    "decode_canonical",
]
