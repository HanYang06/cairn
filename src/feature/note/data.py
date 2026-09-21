# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记数据块 ``NoteData``：**载体**（字段 + 内容视图），不含任何编辑操作。

``body`` 无标记即自证类型（``NoteBody`` 继承 ``Body``）；``style`` 是 ``body.style`` 的代理。
创建 / 落盘 / 版本 / 关系 / 编辑等**操作与策略**全在域服务 :class:`feature.note.service.Note`。
"""

from __future__ import annotations

import copy
from typing import Any, ClassVar

from core.storage import Attr, Block
from core.types import Oid

from ..shared.base import normalize_tags
from ..shared.signature import Signature
from .body import NoteBody
from .edit import (
    StyleMap,
    coerce_style,
    encode_style,
)
from .model import NOTE_KIND, NOTE_MIME, NOTE_SCHEMA


def canvas_ref(index: int) -> dict[str, int]:
    """正文里的画板占位：指向 ``canvas`` 列表的第 ``index`` 块。"""
    return {"canvas": index}


def access_ref(index: int) -> dict[str, int]:
    """正文里的多媒体占位：指向 ``access`` 列表的第 ``index`` 项。"""
    return {"access": index}


class NoteData(Block):
    """笔记数据块：正文容器 + 画板 + 多媒体 + 属性（纯数据）。"""

    type = NOTE_KIND
    mime: ClassVar[str | None] = NOTE_MIME

    body: NoteBody = NoteBody()
    canvas: list[str] = []  # noqa: RUF012  # 画板：存 Canvas 的 oid（全局去重）
    access: list[str] = []  # noqa: RUF012  # 外联资源：存 Asset 的 oid（全局去重）

    # 属性（正文之外，全在这里）：注解即类型，右边即默认值
    schema: Attr[int] = NOTE_SCHEMA
    title: Attr[str | None] = None
    tags: Attr = Attr(factory=dict, coerce=normalize_tags)  # coerce → 显式
    authors: Attr[list[Any]] = []  # noqa: RUF012
    signature: Attr[Signature] = Signature()
    privacy: Attr[str] = ""
    favorite: Attr[bool] = False
    archived: Attr[bool] = False
    trashed: Attr[bool] = False

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # 上次落盘基线；域服务 ``save()`` 据此记版本检查点
        self._saved_state: dict[str, Any] | None = None

    # ---- 去重键（剥离行 id；只算正文 + 行内样式）----
    def body_hash(self) -> str:
        return self.body.refresh().hash

    # ---- 正文读视图 ----
    @property
    def text(self) -> str:
        return self.body.plain

    @property
    def style(self) -> StyleMap:
        return self.body.style

    @style.setter
    def style(self, value: Any) -> None:
        self.body.style = coerce_style(value, self.body.text)
        self.body.refresh()

    def paragraph(self, line_id: str) -> dict[str, Any]:
        """取某行的段落属性。"""
        for line in self.body.text:
            if line["id"] == line_id:
                return dict(line.get("p") or {})
        return {}

    @property
    def references(self) -> tuple[Oid, ...]:
        """正文里引用到的外联资源（``access`` 里的 asset oid）。"""
        return tuple(Oid.parse(str(oid)) for oid in self.access if oid)

    # ---- 版本状态（域服务用）----
    def _state(self) -> dict[str, Any]:
        return {
            "body": [
                {
                    "id": line["id"],
                    "v": copy.deepcopy(line["v"]),
                    **({"p": copy.deepcopy(line["p"])} if line.get("p") else {}),
                }
                for line in self.body.text
            ],
            "style": encode_style(self.body.style),
        }


__all__ = ["NoteData", "access_ref", "canvas_ref"]
