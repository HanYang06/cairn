# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记数据块 ``NoteData``：正文容器 + 画板 / 多媒体引用 + 属性（**载体**）。

``body`` 无标记即自证类型（``NoteBody`` 继承 ``Body``）；``style`` 是 ``body.style`` 的代理。
创建 / 落盘 / 版本 / 关系等**机制与策略**在域服务 :class:`feature.note.service.Note`。
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING, Any, ClassVar, Self

from core.storage import Attr, Block
from core.types import Oid

from ..shared.base import normalize_tags
from ..shared.signature import Signature
from .body import NoteBody
from .edit import (
    OVERLONG_WEIGHT,
    StyleMap,
    apply_text,
    clear_range_style,
    coerce_style,
    drop_style,
    encode_style,
    insert_line,
    is_marker,
    line_styles,
    merge_line,
    merge_style,
    new_id,
    normalize_body,
    remove_line,
    set_line_text,
    set_range_style,
    split_line,
    split_style,
    text_weight,
    toggle_range_style,
)
from .model import NOTE_KIND, NOTE_MIME, NOTE_SCHEMA

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def canvas_ref(index: int) -> dict[str, int]:
    """正文里的画板占位：指向 ``canvas`` 列表的第 ``index`` 块。"""
    return {"canvas": index}


def access_ref(index: int) -> dict[str, int]:
    """正文里的多媒体占位：指向 ``access`` 列表的第 ``index`` 项。"""
    return {"access": index}


class NoteData(Block):
    """笔记数据块：正文容器 + 画板 + 多媒体 + 属性（纯数据 + 纯内容操作）。"""

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

    # ---- 正文 ----
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

    def set_text(self, text: str) -> None:
        """整段替换文字；行 id 与嵌入占位尽量保留。"""
        self.body.text = apply_text(self.body.text, text)
        self.body.refresh()

    def set_body(
        self,
        lines: Sequence[Mapping[str, Any]],
        *,
        style: Mapping[str, Any] | None = None,
    ) -> Self:
        """整段替换正文（编辑器回写用）：行序列 + 可选行内样式。"""
        self.body.text = normalize_body(lines)
        if style is not None:
            self.body.style = coerce_style(style, self.body.text)
        self.body.refresh()
        return self

    def blocks(self) -> list[dict[str, Any]]:
        """给界面用的块视图：行 + 行内样式段 + 段落属性 + 等效字数。"""
        blocks: list[dict[str, Any]] = []
        for line in self.body.text:
            value = line["v"]
            para = dict(line.get("p") or {})
            if is_marker(value):
                kind = "canvas" if "canvas" in value else "access"
                blocks.append(
                    {
                        "id": line["id"],
                        "kind": kind,
                        "text": "",
                        "styles": [],
                        "index": int(value.get(kind, 0)),
                        "para": para,
                        "weight": 0.0,
                    }
                )
                continue
            styles = [
                [start, end, style.to_data()] for start, end, style in line_styles(self.style, line)
            ]
            weight = text_weight(str(value))
            blocks.append(
                {
                    "id": line["id"],
                    "kind": "text",
                    "text": value,
                    "styles": styles,
                    "index": -1,
                    "para": para,
                    "weight": weight,
                    "overlong": weight > OVERLONG_WEIGHT,
                }
            )
        return blocks

    def reorder(self, order: Sequence[int]) -> None:
        """按旧下标顺序重排行；样式按行 id 自动跟随。"""
        lines = list(self.body.text)
        self.body.text = [lines[index] for index in order]
        self.body.refresh()

    # ---- 行级编辑（编辑器接线用；只改内存，落盘由域服务 save 负责）----
    def set_line(self, line_id: str, text: str) -> Self:
        """改写某一行文字（含换行时就地拆行）。"""
        self.body.text = set_line_text(self.body.text, line_id, text)
        self.body.refresh()
        return self

    def insert_line_after(self, line_id: str | None, text: str = "") -> str:
        """在某行之后插入一行（``None`` 追加末尾），返回新行 id。"""
        self.body.text, new_lid = insert_line(self.body.text, line_id, text)
        self.body.refresh()
        return new_lid

    def remove_line(self, line_id: str) -> Self:
        """删除一行；其样式一并丢弃。"""
        self.body.text = remove_line(self.body.text, line_id)
        self.body.style = drop_style(self.body.style, line_id)
        self.body.refresh()
        return self

    def split_line(self, line_id: str, offset: int) -> str:
        """在某行 ``offset`` 处拆行；样式按位置切开。返回新行 id。"""
        self.body.text, new_lid, _, _ = split_line(self.body.text, line_id, offset)
        self.body.style = split_style(self.body.style, line_id, new_lid, int(offset))
        self.body.refresh()
        return new_lid

    def merge_line(self, line_id: str) -> str | None:
        """把某行并入上一行（上一行文字在前）；首行或涉及占位时不合并。

        返回合并后的行 id（未合并返回 ``None``）。调用方可据此把光标移回去。
        """
        lines, prev_id, prev_len = merge_line(self.body.text, line_id)
        if prev_id is None:
            return None
        self.body.text = lines
        self.body.style = merge_style(self.body.style, prev_id, line_id, prev_len)
        self.body.refresh()
        return prev_id

    def toggle_style(self, line_id: str, start: int, end: int, key: str) -> Self:
        """对某行 ``[start, end)`` 切换布尔样式（bold / italic / underline / strike）。"""
        toggled = toggle_range_style(self.body.style, line_id, start, end, key)
        self.body.style = coerce_style(toggled, self.body.text)
        self.body.refresh()
        return self

    def set_style_span(self, line_id: str, start: int, end: int, patch: Mapping[str, Any]) -> Self:
        """对某行 ``[start, end)`` 设置若干行内样式字段（颜色 / 字号 / 字体 / 布尔）。"""
        changed = set_range_style(self.body.style, line_id, start, end, patch)
        self.body.style = coerce_style(changed, self.body.text)
        self.body.refresh()
        return self

    def clear_style_span(self, line_id: str, start: int, end: int) -> Self:
        """清掉某行 ``[start, end)`` 的全部行内样式。"""
        changed = clear_range_style(self.body.style, line_id, start, end)
        self.body.style = coerce_style(changed, self.body.text)
        self.body.refresh()
        return self

    # ---- 段落属性（行级；一行 = 一段）----
    def paragraph(self, line_id: str) -> dict[str, Any]:
        """取某行的段落属性。"""
        for line in self.body.text:
            if line["id"] == line_id:
                return dict(line.get("p") or {})
        return {}

    def set_paragraph(self, line_id: str, patch: Mapping[str, Any]) -> Self:
        """合并段落属性；值为 ``None`` / 空串 / 空列表则删除该键。"""
        for line in self.body.text:
            if line["id"] != line_id:
                continue
            para = dict(line.get("p") or {})
            for key, value in patch.items():
                if value in (None, "", [], {}):
                    para.pop(key, None)
                else:
                    para[key] = value
            if para:
                line["p"] = para
            else:
                line.pop("p", None)
            break
        self.body.refresh()
        return self

    def clear_paragraph(self, line_id: str) -> Self:
        """清掉某行的全部段落属性。"""
        return self.set_paragraph(line_id, dict.fromkeys(self.paragraph(line_id)))

    # ---- 画板 / 外联资源嵌入（只改内存，落盘由域服务负责）----
    @property
    def references(self) -> tuple[Oid, ...]:
        """正文里引用到的外联资源（``access`` 里的 asset oid）。"""
        return tuple(Oid.parse(str(oid)) for oid in self.access if oid)

    def _append_marker(self, marker: dict[str, int]) -> None:
        self.body.text = [*self.body.text, {"id": new_id(), "v": marker}]
        self.body.refresh()

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
