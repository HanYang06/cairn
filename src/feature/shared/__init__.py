# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""共享件：**非域**的跨域内容。

- 存储数据结构：`asset` / `canvas` / `group`
- 共享值：`signature`
- 共享设施：`relation`（边表）/ `provenance`（血缘查询，降级）/ `base`（错误 / 标签）

域（`feature.note` / `feature.project`）按需引用；这里**不 import 任何域**。
"""

from __future__ import annotations

from .asset import AssetData
from .base import (
    UNSET,
    DomainError,
    KindMismatchError,
    UnknownKindError,
    known_kinds,
    normalize_tags,
)
from .canvas import CanvasBody, CanvasData, Form, Graphic, Line, Link, Paint
from .group import GroupData, GroupError, all_gids, list_groups, roots
from .provenance import ancestors, derivatives, descendants, lineage
from .relation import Relation
from .signature import Signature

__all__ = [
    "UNSET",
    "AssetData",
    "CanvasBody",
    "CanvasData",
    "DomainError",
    "Form",
    "Graphic",
    "GroupData",
    "GroupError",
    "KindMismatchError",
    "Line",
    "Link",
    "Paint",
    "Relation",
    "Signature",
    "UnknownKindError",
    "all_gids",
    "ancestors",
    "derivatives",
    "descendants",
    "known_kinds",
    "lineage",
    "list_groups",
    "normalize_tags",
    "roots",
]
