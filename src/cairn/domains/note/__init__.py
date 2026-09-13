# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：节点 + 基板。

无强制"标题/正文"字段：标题是可空元数据，正文是可扩展的片段序列。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Self

from ...types import Oid, SpaceId
from ..base import UNSET, DomainObject, get_handler, register
from ..types import (
    decode_substrate,
    embed_fragment,
    encode_substrate,
    plain_text,
    referenced_oids,
    text_fragment,
)

if TYPE_CHECKING:
    from ..relation import Relation

NOTE_KIND = "cairn.note"
NOTE_MIME = "application/x-cairn-note"
NOTE_SCHEMA = 1


def _search_text(title: str | None, text: str) -> str:
    return f"{title or ''}\n{text}"


class NoteHandler:
    kind: str = NOTE_KIND
    schema_version: int = NOTE_SCHEMA

    def normalize_meta(self, **fields: Any) -> dict[str, Any]:
        title = fields.get("title")
        tags = fields.get("tags") or ()
        props = fields.get("props") or {}
        return {
            "title": None if title is None else str(title),
            "tags": [str(tag) for tag in tags],
            "schema": NOTE_SCHEMA,
            "props": dict(props),
        }


register(NoteHandler())


class Note(DomainObject):
    kind: ClassVar[str] = NOTE_KIND
    mime: ClassVar[str | None] = NOTE_MIME
    schema_version: ClassVar[int] = NOTE_SCHEMA

    @classmethod
    def create(
        cls,
        vault: Any,
        text: str = "",
        *,
        title: str | None = None,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
        space: str | SpaceId = "default",
    ) -> Self:
        meta = get_handler(cls.kind).normalize_meta(title=title, tags=tags, props=props)
        payload = encode_substrate([text_fragment(text)])
        oid = vault.put(
            payload,
            space=space,
            type=cls.kind,
            mime=cls.mime,
            meta=meta,
            search_text=_search_text(title, text),
        )
        return cls.load(vault, oid)

    @property
    def text(self) -> str:
        return plain_text(self.fragments)

    @property
    def fragments(self) -> list[dict[str, Any]]:
        return decode_substrate(self.read())

    @property
    def embeds(self) -> list[dict[str, Any]]:
        return [fragment for fragment in self.fragments if fragment.get("kind") == "embed"]

    @property
    def references(self) -> tuple[Oid, ...]:
        return referenced_oids(self.fragments)

    def update(
        self,
        *,
        text: str | None = None,
        title: str | None = UNSET,
        tags: list[str] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        current = self.meta()
        merged_props = dict(current.get("props") or {})
        if props:
            merged_props.update(props)
        new_title = current.get("title") if title is UNSET else title
        new_tags = list(current.get("tags") or ()) if tags is None else list(tags)
        meta = get_handler(self.kind).normalize_meta(
            title=new_title, tags=new_tags, props=merged_props
        )
        new_text = self.text if text is None else text
        search_text = _search_text(new_title, new_text)
        # 只有正文（内容）变化才产生版本；标题/标签/props 仅改元数据。
        if text is not None and text != self.text:
            payload = encode_substrate([text_fragment(text)])
            self._put(payload, meta=meta, search_text=search_text)
        else:
            self._put_meta(meta=meta, search_text=search_text)
        self._refresh()
        return self

    def add_embed(
        self,
        oid: Oid | str,
        *,
        role: str = "embed",
        caption: str | None = None,
    ) -> Self:
        fragments = self.fragments
        fragments.append(embed_fragment(oid, role=role, caption=caption))
        self._rewrite(fragments)
        return self

    def link(self, target: Oid | str, relation: str = "references") -> Relation:
        from ..relation import Relation

        return Relation.create(
            self._vault,
            self._oid,
            target,
            relation=relation,
            space=self._info.space_id,
        )

    def _rewrite(self, fragments: list[dict[str, Any]]) -> None:
        current = self.meta()
        meta = get_handler(self.kind).normalize_meta(
            title=current.get("title"),
            tags=current.get("tags"),
            props=current.get("props"),
        )
        self._put(encode_substrate(fragments), meta=meta)
        self._refresh()
