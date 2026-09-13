# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域层：笔记 / 存储 / 项目。共享核心底座，各自持有 schema。

包组织：
  base.py        领域基类 + 处理器注册表
  substrate.py   基板格式（多模态片段）
  relation.py    关系（跨领域，一等对象）
  composition.py 组装（文档 / 博客）
  note.py        笔记
  asset.py       资产（存储）
  project.py     项目
  provenance.py  笔记衍生关系（派生遍历）
"""

from __future__ import annotations

from .asset import Asset
from .base import (
    DomainError,
    DomainObject,
    Handler,
    KindMismatchError,
    UnknownKindError,
    get_handler,
    known_kinds,
    register,
)
from .composition import Composition
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
    "Composition",
    "DomainError",
    "DomainObject",
    "Handler",
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
    "get_handler",
    "known_kinds",
    "lineage",
    "plain_text",
    "ref_fragment",
    "referenced_oids",
    "register",
    "text_fragment",
]
