# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域层：note / asset / project / relation。

每个领域都**继承 ``Block``**；自己的数据结构放各自的 ``types``，行为放各自模块。
组装（文档 / 博客）不再是独立对象——它就是"正文里放一堆引用"的 note。
"""

from __future__ import annotations

from .asset import Asset
from .base import (
    DomainError,
    KindMismatchError,
    UnknownKindError,
    known_kinds,
)
from .note import Note
from .project import Project
from .provenance import ancestors, derivatives, descendants, lineage
from .relation import Relation
from .types import (
    decode_substrate,
    embed_fragment,
    encode_substrate,
    plain_text,
    ref_fragment,
    referenced_oids,
    text_fragment,
)

__all__ = [
    "Asset",
    "DomainError",
    "KindMismatchError",
    "Note",
    "Project",
    "Relation",
    "UnknownKindError",
    "ancestors",
    "decode_substrate",
    "derivatives",
    "descendants",
    "embed_fragment",
    "encode_substrate",
    "known_kinds",
    "lineage",
    "plain_text",
    "ref_fragment",
    "referenced_oids",
    "text_fragment",
]
