# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组装领域：继承 ``Block`` 的文档 / 博客 = 对其它对象的排布（transclusion）。"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Self

from ..core.store import Attr, Block, Body
from ..types import Oid

COMPOSITION_KIND = "cairn.composition"
COMPOSITION_SCHEMA = 1


class Composition(Block):
    type = COMPOSITION_KIND
    body = Body(factory=list)

    schema = Attr(default=COMPOSITION_SCHEMA)

    @classmethod
    def create(
        cls,
        vault: Any,
        items: Iterable[Oid | str] = (),
        *,
        title: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
        space: Any = None,
    ) -> Self:
        del space
        document = cls()
        document._vault = vault
        document.title = title
        merged = dict(props or {})
        merged["items"] = [str(item) for item in items]
        document.attrs["props"] = merged
        document.tags = tags or {}
        document.save()
        return document

    @property
    def items(self) -> tuple[Oid, ...]:
        return tuple(
            Oid.parse(str(item)) for item in (self.props().get("items") or ())
        )


__all__ = ["COMPOSITION_KIND", "COMPOSITION_SCHEMA", "Composition"]
