# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域共享层：横跨多域的共享设施（**非域**）。

域只向下依赖本层，**域之间不互相 import**。`relation` = 通用跨域边；`signature` = 签名值类型；
`provenance` = 基于边的拓扑查询。
"""

from __future__ import annotations

from .provenance import ancestors, derivatives, descendants, lineage
from .relation import Relation
from .signature import Signature

__all__ = [
    "Relation",
    "Signature",
    "ancestors",
    "derivatives",
    "descendants",
    "lineage",
]
