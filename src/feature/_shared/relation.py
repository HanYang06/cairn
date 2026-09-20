# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""关系领域：**一等 DB 行**（不是块），承载笔记之间的各种关联。

关系类型（``kind``）不是只有"派生"一种：
    derived-from   派生 / 再创作（谁基于谁）
    references     引用（论文式引用，用于拓扑）
    contains       项目成员 / 归属
    …              可继续加

关系落 ``relations`` 表，便于按上下游查询、绘制引用拓扑。
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from typing import Any, ClassVar

from core.storage import canonical, decode_canonical
from core.types import KindMismatchError, Oid, now_ms

RELATION_KIND = "cairn.relation"
RELATION_SCHEMA = 1

DERIVED_FROM = "derived-from"
REFERENCES = "references"
CONTAINS = "contains"

_TABLE = "relation"
_COLUMNS = {
    "id": "TEXT PRIMARY KEY",
    "src": "TEXT NOT NULL",
    "dst": "TEXT NOT NULL",
    "kind": "TEXT NOT NULL",
    "domain": "TEXT NOT NULL DEFAULT ''",
    "at": "TEXT",
    "attrs": "BLOB",
    "created": "INTEGER NOT NULL",
}


def _table(vault: Any) -> Any:
    return vault.bucket.table(_TABLE, **_COLUMNS)


class Relation:
    """一条关系行：``src --kind--> dst``。"""

    kind: ClassVar[str] = RELATION_KIND

    def __init__(  # noqa: PLR0913, PLR0917 — 关系行的扁平字段构造器
        self,
        vault: Any,
        id: str,
        src: str,
        dst: str,
        kind: str,
        domain: str = "",
        at: str | None = None,
        attrs: dict[str, Any] | None = None,
        created: int = 0,
    ) -> None:
        self._vault = vault
        self.id = id
        self._src = src
        self._dst = dst
        self._kind = kind
        self._domain = domain
        self._at = at
        self._attrs = dict(attrs or {})
        self.created = created

    # ---- 视图 ----
    @property
    def oid(self) -> Oid:
        return Oid.parse(self.id)

    @property
    def source(self) -> Oid:
        return Oid.parse(self._src)

    @property
    def target(self) -> Oid:
        return Oid.parse(self._dst)

    @property
    def relation(self) -> str:
        return self._kind

    @property
    def domain(self) -> str:
        """该边归属的领域类型（note / project / group …）。"""
        return self._domain

    @property
    def at(self) -> str | None:
        """该边所钉的被派生版本；无则 None。"""
        return self._at

    def props(self) -> dict[str, Any]:
        return dict(self._attrs)

    def tags(self) -> dict[str, Any]:
        return dict(self._attrs.get("tags") or {})

    # ---- 写 ----
    @classmethod
    def create(  # noqa: PLR0913 — 建边入口：描述字段均有默认值
        cls,
        vault: Any,
        source: Oid | str,
        target: Oid | str,
        relation: str = REFERENCES,
        *,
        domain: str = "",
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Relation:
        rid = str(Oid.new())
        attrs = dict(props or {})
        at = attrs.pop("at", None)
        if tags:
            attrs["tags"] = (
                {str(key): value for key, value in tags.items()}
                if isinstance(tags, Mapping)
                else {str(item): None for item in tags}
            )
        _table(vault).insert(
            {
                "id": rid,
                "src": str(source),
                "dst": str(target),
                "kind": str(relation),
                "domain": str(domain),
                "at": None if at is None else str(at),
                "attrs": canonical(attrs),
                "created": now_ms(),
            }
        )
        vault.bucket.commit()
        return cls.load(vault, rid)

    # ---- 读 ----
    @classmethod
    def load(cls, vault: Any, oid: Oid | str) -> Relation:
        rows = _table(vault).select(id=str(oid))
        if not rows:
            raise KindMismatchError(f"{oid} 不是关系")
        return cls._from_row(vault, rows[0])

    @classmethod
    def _from_row(cls, vault: Any, row: Any) -> Relation:
        raw = row["attrs"]
        attrs = decode_canonical(bytes(raw)) if raw else {}
        return cls(
            vault,
            str(row["id"]),
            str(row["src"]),
            str(row["dst"]),
            str(row["kind"]),
            str(row["domain"] or ""),
            row["at"],
            attrs,
            int(row["created"]),
        )

    @classmethod
    def list(cls, vault: Any) -> Iterator[Relation]:
        for row in _table(vault).all():
            yield cls._from_row(vault, row)

    @classmethod
    def outbound(
        cls,
        vault: Any,
        source: Oid | str,
        *,
        relation: str | None = None,
    ) -> Iterator[Relation]:
        for row in _table(vault).select(src=str(source)):
            item = cls._from_row(vault, row)
            if relation is None or item.relation == relation:
                yield item

    @classmethod
    def backlinks(
        cls,
        vault: Any,
        target: Oid | str,
        *,
        relation: str | None = None,
    ) -> Iterator[Relation]:
        for row in _table(vault).select(dst=str(target)):
            item = cls._from_row(vault, row)
            if relation is None or item.relation == relation:
                yield item


__all__ = [
    "CONTAINS",
    "DERIVED_FROM",
    "REFERENCES",
    "RELATION_KIND",
    "RELATION_SCHEMA",
    "Relation",
]
