# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""新存储层：桶 + 块。

只有两个概念：

    Bucket  载体——受管的文件系统，**类**，不是数据结构
    Block   存储单元——``{id, checksum, type, body, attrs}``

其余一切（笔记 / 项目 / 多媒体 / 索引 / 变更）都是块的一种 ``type`` / ``body``。
"""

from __future__ import annotations

from .block import (
    BLOCK_VERSION,
    INDEX_TYPE,
    PART_TYPE,
    Attr,
    Block,
    Body,
    canonical,
    decode_canonical,
)
from .bucket import CATALOG_NAME, Bucket, BucketConfig
from .catalog import BlockLocation, Catalog
from .table import Table

__all__ = [
    "BLOCK_VERSION",
    "CATALOG_NAME",
    "INDEX_TYPE",
    "PART_TYPE",
    "Attr",
    "Block",
    "BlockLocation",
    "Body",
    "Bucket",
    "BucketConfig",
    "Catalog",
    "Table",
    "canonical",
    "decode_canonical",
]
