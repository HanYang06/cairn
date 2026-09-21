# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域层：**域**（Note / Project）+ **存储数据结构**（note / canvas / asset / group 数据块）。

- **域** = ``Domain`` 子类：管理型、单例、无 ID；管配置、给 UI API。
- **数据结构** = ``Block`` 子类：有 ID 的纯数据块（画板 / 资产 / 组…），由域按需使用。
- 组装（文档 / 博客）不再是独立对象——它就是"正文里放一堆引用"的 note。
"""

from __future__ import annotations

from .asset import AssetData
from .base import (
    DomainError,
    KindMismatchError,
    UnknownKindError,
    known_kinds,
    normalize_tags,
)
from .canvas import CanvasBody, CanvasData, Form, Graphic, Line, Link, Paint
from .group import GroupData, GroupError, all_gids, list_groups, roots
from .note import Note, NoteData
from .project import Project, ProjectData
from .provenance import ancestors, derivatives, descendants, lineage
from .relation import Relation
from .signature import Signature

__all__ = [
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
    "Note",
    "NoteData",
    "Paint",
    "Project",
    "ProjectData",
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
