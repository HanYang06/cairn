# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""领域层：**域**（Note / Project）+ **共享件**（`shared/`）。

- **域** = ``Domain`` 子类：管理型、单例、无 ID；管配置、给 UI API。
- **共享件** = ``shared/``：非域的跨域内容（asset / canvas / group / signature / relation /
  provenance / base）。
- 组装（文档 / 博客）不再是独立对象——它就是"正文里放一堆引用"的 note。
"""

from __future__ import annotations

from .note import Note, NoteData
from .project import Project, ProjectData
from .shared import (
    AssetData,
    CanvasBody,
    CanvasData,
    DomainError,
    Form,
    Graphic,
    GroupData,
    GroupError,
    Kind,
    KindMismatchError,
    Line,
    Link,
    Paint,
    Relation,
    Signature,
    UnknownKindError,
    all_gids,
    ancestors,
    derivatives,
    descendants,
    known_kinds,
    lineage,
    list_groups,
    normalize_tags,
    roots,
)

__all__ = [
    "AssetData",
    "CanvasBody",
    "CanvasData",
    "DomainError",
    "Form",
    "Graphic",
    "GroupData",
    "GroupError",
    "Kind",
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
