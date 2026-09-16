# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：正文 = **行序列 + 行内区间样式**，版本走通用 ``VersionStore``。

正文形态：
    body  = [ {"id": lid, "v": "第一行"}, {"id": lid2, "v": {"canvas": 0}} ]
    style = { lid: [ {(0, 3): Style(bold=True)} ] }        # 行内区间，丢行 id 进摘要

- 行 id 稳定锚点，样式/版本都按它寻址，行增删不漂移。
- 内容签名（cID 用的 checksum）**剥离行 id**：同文同样式 → 同签名 → 可去重；
  改一个字则签名不同，天然不去重。
- 版本由 ``VersionStore`` + ``versions.NOTE_CODEC`` 承载，本类只做接线。
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, ClassVar, Self

from ...core.store import Attr, Block, VersionStore
from ...types import Oid
from ..base import UNSET
from .edit import Line as LineDict
from .edit import (
    StyleMap,
    apply_text,
    coerce_style,
    encode_style,
    flatten_text,
    is_marker,
    new_id,
    normalize_body,
    signature_style,
)
from .model import (
    NOTE_KIND,
    NOTE_MIME,
    NOTE_SCHEMA,
    Access,
    Canvas,
    Form,
    Graphic,
    Line,
    Link,
    Paint,
    Segment,
    Style,
)
from .versions import NOTE_CODEC


def canvas_ref(index: int) -> dict[str, int]:
    """正文里的画板占位：指向 ``canvas`` 列表的第 ``index`` 块。"""
    return {"canvas": index}


def access_ref(index: int) -> dict[str, int]:
    """正文里的多媒体占位：指向 ``access`` 列表的第 ``index`` 项。"""
    return {"access": index}


class NoteBody:
    """``body`` 的声明：始终返回带 id 的行序列。"""

    def __get__(self, obj: Block | None, _owner: type | None = None) -> Any:
        if obj is None:
            return self
        if "_body" not in obj.__dict__:
            obj.__dict__["_body"] = normalize_body([])
        return obj.__dict__["_body"]

    def __set__(self, obj: Block, value: Any) -> None:
        obj.__dict__["_body"] = normalize_body(value)


class NoteStyle:
    """``style`` 的声明：类型化样式表，落盘在 ``attrs['style']``。"""

    def __get__(self, obj: Block | None, _owner: type | None = None) -> Any:
        if obj is None:
            return self
        return coerce_style(obj.attrs.get("style"), obj.__dict__.get("_body") or [])

    def __set__(self, obj: Block, value: Any) -> None:
        lines = obj.__dict__.get("_body") or normalize_body([])
        encoded = encode_style(coerce_style(value, lines))
        if encoded:
            obj.attrs["style"] = encoded
        else:
            obj.attrs.pop("style", None)


class Note(Block):
    """笔记块：行序列正文 + 行内样式 + 画板 + 多媒体 + 属性。"""

    type = NOTE_KIND
    mime: ClassVar[str | None] = NOTE_MIME

    body = NoteBody()
    style = NoteStyle()
    canvas: list[Canvas] = Attr(factory=list, item=Canvas)  # type: ignore[assignment]
    access: list[Access] = Attr(factory=list, item=Access)  # type: ignore[assignment]

    # 属性（正文之外，全在这里）
    schema = Attr(default=NOTE_SCHEMA)
    signature = Attr(default="")            # 创作签名（创建即锁死）
    privacy = Attr(default="")              # 隐私状态
    derived = Attr(factory=list)            # 派生关系列表（旧字段，派生已走关系表）
    authors = Attr(factory=list)            # 署名作者（有序：一作、二作…）；author 是原作者
    favorite = Attr(default=False)
    archived = Attr(default=False)
    trashed = Attr(default=False)
    share = Attr(factory=list)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # 上次落盘时的版本状态；``save()`` 以此为基线记版本
        self._saved_state: dict[str, Any] | None = None

    # ---- 内容签名（剥离行 id）----
    def content(self) -> dict[str, Any]:
        attrs = {key: value for key, value in self.attrs.items() if key != "style"}
        style_view = signature_style(self.body, self.style)
        if any(style_view):
            attrs["style"] = style_view
        return {
            "type": self.type,
            "body": [line["v"] for line in self.body],
            "attrs": attrs,
        }

    # ---- 读写 ----
    @classmethod
    def load(cls, vault: Any, oid: Oid | str) -> Self:
        note = super().load(vault, oid)
        note._saved_state = note._state()
        return note

    def save(self, *, search_text: str | None = None) -> Self:
        if search_text is None:
            search_text = _search_text(self.title, self.text)
        previous = self._saved_state
        super().save(search_text=search_text)
        store = VersionStore(self._require_vault().bucket)
        if previous is None:
            store.root(self.id, NOTE_CODEC, self._state())
        else:
            current = self._state()
            if current != previous:
                store.commit(self.id, NOTE_CODEC, previous, current)
        self._saved_state = self._state()
        return self

    @classmethod
    def create(
        cls,
        vault: Any,
        text: str = "",
        *,
        title: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        note = cls()
        note._vault = vault
        note.set_text(text)
        note.title = title
        note.tags = tags or {}
        if props:
            note.attrs["props"] = dict(props)
        note.save(search_text=_search_text(title, text))
        return note

    # ---- 正文 ----
    @property
    def text(self) -> str:
        return flatten_text(self.body)

    def set_text(self, text: str) -> None:
        """整段替换文字；行 id 与嵌入占位尽量保留。"""
        self.body = apply_text(self.body, text)

    def reorder(self, order: Sequence[int]) -> None:
        """按旧下标顺序重排行；样式按行 id 自动跟随。"""
        lines = list(self.body)
        self.body = [lines[index] for index in order]

    # ---- 画板 / 多媒体嵌入 ----
    @property
    def references(self) -> tuple[Oid, ...]:
        """正文里引用到的多媒体对象（``access`` 里的 oid）。"""
        return tuple(Oid.parse(item.oid) for item in self.access if item.oid)

    def add_canvas(self, canvas: Canvas) -> Canvas:
        """把一块画板嵌进正文：追加到 ``canvas``，并在 body 末尾放占位。"""
        self.canvas = [*self.canvas, canvas]
        self._append_marker(canvas_ref(len(self.canvas) - 1))
        return canvas

    def add_access(
        self,
        oid: Oid | str,
        *,
        mime: str = "",
        name: str = "",
        size: float = 0.0,
    ) -> Access:
        """把一段多媒体嵌进正文：追加到 ``access``，并在 body 末尾放占位。"""
        entry = Access(oid=str(oid), mime=mime, name=name, size=size)
        self.access = [*self.access, entry]
        self._append_marker(access_ref(len(self.access) - 1))
        return entry

    def _append_marker(self, marker: dict[str, int]) -> None:
        self.body = [*self.body, {"id": new_id(), "v": marker}]
        if self._vault is not None:
            self.save()

    # ---- 属性 ----
    def update(
        self,
        *,
        text: str | None = None,
        title: str | None = UNSET,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> Self:
        merged = self.props()
        if props:
            merged.update(props)
        if title is not UNSET:
            self.title = title
        if tags is not None:
            self.tags = tags
        self.attrs["props"] = merged
        if text is not None:
            self.set_text(text)
        self.save(search_text=_search_text(self.title, self.text))
        return self

    def link(self, target: Oid | str, relation: str = "references") -> Any:
        from ..relation import Relation

        return Relation.create(self._require_vault(), self.oid, target, relation=relation)

    # ---- 版本（走通用引擎）----
    def _state(self) -> dict[str, Any]:
        return {
            "body": [{"id": line["id"], "v": copy.deepcopy(line["v"])} for line in self.body],
            "style": encode_style(self.style),
        }

    def history(self) -> list[dict[str, Any]]:
        if self._vault is None:
            return []
        return VersionStore(self._vault.bucket).history(self.id)

    def body_at(self, version: str) -> list[LineDict]:
        if self._vault is None:
            return list(self.body)
        state = VersionStore(self._vault.bucket).state_at(
            self.id, NOTE_CODEC, self._state(), str(version)
        )
        return state["body"]

    def restore(self, version: str) -> Self:
        """把指定版本的正文/样式作为新版本写回（历史继续向前）。"""
        if self._vault is None:
            return self
        state = VersionStore(self._vault.bucket).state_at(
            self.id, NOTE_CODEC, self._state(), str(version)
        )
        self.body = state["body"]
        self.style = state["style"]
        self.save()
        return self


def _search_text(title: str | None, text: str) -> str:
    return f"{title or ''}\n{text}"


__all__ = [
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "Access",
    "Canvas",
    "Form",
    "Graphic",
    "Line",
    "LineDict",
    "Link",
    "Note",
    "NoteBody",
    "NoteStyle",
    "Paint",
    "Segment",
    "Style",
    "StyleMap",
    "access_ref",
    "canvas_ref",
    "is_marker",
]
