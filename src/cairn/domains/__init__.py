"""领域层：笔记 / 存储 / 项目。共享核心底座，各自持有 schema。

当前实现：Note（节点 + 基板）、Relation（一等关系对象）、Composition（组装）。
"""

from __future__ import annotations

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
from .relation import Relation
from .substrate import (
    decode_substrate,
    encode_substrate,
    plain_text,
    ref_fragment,
    text_fragment,
)

__all__ = [
    "Composition",
    "DomainError",
    "DomainObject",
    "Handler",
    "KindMismatchError",
    "Note",
    "Relation",
    "UnknownKindError",
    "decode_substrate",
    "encode_substrate",
    "get_handler",
    "known_kinds",
    "plain_text",
    "ref_fragment",
    "register",
    "text_fragment",
]
