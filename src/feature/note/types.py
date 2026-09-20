# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域：**数据**（``NoteData``）与**域服务**（``Note``）分离。

- ``NoteData(Block)``：正文容器 + 画板 + 多媒体 + 属性；只做**纯内容操作**（不落盘）。
- ``Note(Domain)``：笔记域服务（单例）：创建 / 读写 / 落盘 / 版本 / 关系 / 策略。
  数据由 **Bucket（存储）与 Note（语义）共同管理，各管各的**。

正文形态：
    body  = [ {"id": lid, "v": "第一行"}, {"id": lid2, "v": {"canvas": 0}} ]
    style = { lid: [ {(0, 3): Style(bold=True)} ] }        # 行内区间，丢行 id 进摘要

- 行 id 稳定锚点，样式/版本都按它寻址，行增删不漂移。
- 内容签名（cID 用的 checksum）**剥离行 id**：同文同样式 → 同签名 → 可去重；
  改一个字则签名不同，天然不去重。
- 版本由 ``VersionStore`` + ``versions.NOTE_CODEC`` 承载，域服务接线。
"""

from __future__ import annotations

import copy
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, ClassVar, Self

from core.signal import Domain, Topic, action
from core.storage import Attr, Block, Body, VersionStore
from core.types import Oid

from ..base import UNSET, normalize_tags
from ..signature import Signature
from .edit import (
    OVERLONG_WEIGHT,
    StyleMap,
    apply_text,
    clear_range_style,
    coerce_style,
    drop_style,
    encode_style,
    flatten_text,
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
    signature_style,
    split_line,
    split_style,
    text_weight,
    toggle_range_style,
)
from .edit import Line as LineDict
from .model import (
    NOTE_KIND,
    NOTE_MIME,
    NOTE_SCHEMA,
    CanvasBody,
    CanvasData,
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


class NoteBody(Body):
    """正文容器：``text``（行序列）+ ``style``（行内样式）；自带状态 ``hash``。

    - 行为像 list（迭代 / 下标 / 长度代理到 ``text`` 的行），方便 ``note.body[0]["v"]``。
    - ``hash`` = 对 ``content()``（行值 + 行内样式，**剥离行 id**）求摘要；
      不含 attrs / 签名 / 时间戳。内容一变就 ``refresh()`` 重算并存起来。
    """

    def __init__(self, text: Any = None, style: Any = None, hash: str = "") -> None:
        self.text: list[LineDict] = normalize_body(text)
        self.style: StyleMap = coerce_style(style, self.text)
        self.hash = str(hash or "")
        if not self.hash:
            self.refresh()

    def content(self) -> dict[str, Any]:
        return {
            "text": [line["v"] for line in self.text],
            "para": [line.get("p") or {} for line in self.text],
            "style": signature_style(self.text, self.style),
        }

    def to_data(self) -> dict[str, Any]:
        return {"text": self.text, "style": encode_style(self.style), "hash": self.hash}

    @classmethod
    def from_data(cls, data: Any) -> NoteBody:
        if not data:
            return cls()
        if isinstance(data, Mapping) and "text" in data:
            return cls(
                text=data.get("text"),
                style=data.get("style"),
                hash=str(data.get("hash") or ""),
            )
        return cls(text=data)  # 兼容：旧 body 就是裸行序列

    @property
    def plain(self) -> str:
        return flatten_text(self.text)

    def refresh(self) -> NoteBody:
        super().refresh()
        return self

    def __iter__(self) -> Any:
        return iter(self.text)

    def __getitem__(self, index: Any) -> Any:
        return self.text[index]

    def __len__(self) -> int:
        return len(self.text)


class NoteData(Block):
    """笔记数据块：正文容器 + 画板 + 多媒体 + 属性（纯数据 + 纯内容操作）。

    ``body`` 无标记即自证类型（``NoteBody`` 继承 ``Body``）；``style`` 是 ``body.style`` 的代理。
    创建 / 落盘 / 版本 / 关系等**机制与策略**在域服务 :class:`Note`。
    """

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
    def set_line(self, line_id: str, text: str) -> NoteData:
        """改写某一行文字（含换行时就地拆行）。"""
        self.body.text = set_line_text(self.body.text, line_id, text)
        self.body.refresh()
        return self

    def insert_line_after(self, line_id: str | None, text: str = "") -> str:
        """在某行之后插入一行（``None`` 追加末尾），返回新行 id。"""
        self.body.text, new_lid = insert_line(self.body.text, line_id, text)
        self.body.refresh()
        return new_lid

    def remove_line(self, line_id: str) -> NoteData:
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

    def toggle_style(self, line_id: str, start: int, end: int, key: str) -> NoteData:
        """对某行 ``[start, end)`` 切换布尔样式（bold / italic / underline / strike）。"""
        toggled = toggle_range_style(self.body.style, line_id, start, end, key)
        self.body.style = coerce_style(toggled, self.body.text)
        self.body.refresh()
        return self

    def set_style_span(
        self, line_id: str, start: int, end: int, patch: Mapping[str, Any]
    ) -> NoteData:
        """对某行 ``[start, end)`` 设置若干行内样式字段（颜色 / 字号 / 字体 / 布尔）。"""
        changed = set_range_style(self.body.style, line_id, start, end, patch)
        self.body.style = coerce_style(changed, self.body.text)
        self.body.refresh()
        return self

    def clear_style_span(self, line_id: str, start: int, end: int) -> NoteData:
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

    def set_paragraph(self, line_id: str, patch: Mapping[str, Any]) -> NoteData:
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

    def clear_paragraph(self, line_id: str) -> NoteData:
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


class Note(Domain):
    """笔记域服务（单例）：创建 / 读写 / 落盘 / 版本 / 关系 / 策略。

    数据（``NoteData``）由本服务与 Bucket 共同管理：Bucket 管存储，本服务管语义。
    """

    name = "Note"

    changed = Topic()

    def __init__(self, vault: Any) -> None:
        self.vault = vault

    # ---- 创建 / 读取 ----
    @action
    def create(
        self,
        text: str = "",
        *,
        title: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> NoteData:
        """新建一条笔记：落盘 + 记根版本，返回其数据。"""
        data = NoteData()
        data._vault = self.vault  # noqa: SLF001 — 服务为数据绑定库，同包强耦合
        data.set_text(text)
        data.title = title
        data.tags = tags or {}
        if props:
            data.attrs["props"] = dict(props)
        # 创作签名：锁在创建时的正文内容上（原始结构据此可找回）
        data.signature = Signature.create(author=data.author or "", subject=data.body_hash())
        self.save(data, search_text=_search_text(title, text))
        return data

    @action
    def load(self, oid: Oid | str) -> NoteData:
        """按 oid 载入一条笔记数据。"""
        data: NoteData = NoteData.load(self.vault, oid)
        data._saved_state = data._state()  # noqa: SLF001 — 记录落盘基线
        return data

    @action
    def list_notes(
        self,
        *,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
    ) -> list[NoteData]:
        """列出笔记数据。"""
        return [self.load(info.oid) for info in self.vault.iter(type=NOTE_KIND, tags=tags)]

    # ---- 落盘 / 版本 ----
    @action
    def save(self, data: NoteData, *, search_text: str | None = None) -> NoteData:
        """落盘并**记一个版本检查点**（内容变了才追加补丁）。"""
        if search_text is None:
            search_text = _search_text(data.title, data.text)
        previous = data._saved_state  # noqa: SLF001 — 域服务持有版本基线
        data.save(search_text=search_text)  # Block.save：块级落盘
        store = VersionStore(self.vault.bucket)
        if previous is None:
            store.root(data.id, NOTE_CODEC, data._state())  # noqa: SLF001
        else:
            current = data._state()  # noqa: SLF001
            if current != previous:
                store.commit(data.id, NOTE_CODEC, previous, current)
        data._saved_state = data._state()  # noqa: SLF001
        self.changed.emit(data.oid)
        return data

    @action
    def persist(self, data: NoteData, *, search_text: str | None = None) -> NoteData:
        """只**落盘当前内容**，不记版本（连续编辑中的自动保存用）。"""
        if search_text is None:
            search_text = _search_text(data.title, data.text)
        data.save(search_text=search_text)
        return data

    @action
    def history(self, data: NoteData) -> list[dict[str, Any]]:
        """版本历史（最新在前）。"""
        return VersionStore(self.vault.bucket).history(data.id)

    @action
    def body_at(self, data: NoteData, version: str) -> list[LineDict]:
        """取指定版本的正文行序列。"""
        state = VersionStore(self.vault.bucket).state_at(
            data.id,
            NOTE_CODEC,
            data._state(),  # noqa: SLF001 — 域服务读取数据内部状态
            str(version),
        )
        body: list[LineDict] = state["body"]
        return body

    @action
    def restore(self, data: NoteData, version: str) -> NoteData:
        """把指定版本的正文/样式作为新版本写回（历史继续向前）。"""
        state = VersionStore(self.vault.bucket).state_at(
            data.id,
            NOTE_CODEC,
            data._state(),  # noqa: SLF001 — 域服务读取数据内部状态
            str(version),
        )
        data.body.text = normalize_body(state["body"])
        data.body.style = coerce_style(state["style"], data.body.text)
        data.body.refresh()
        self.save(data)
        return data

    # ---- 属性 / 关系 / 嵌入 ----
    @action
    def update(
        self,
        data: NoteData,
        *,
        text: str | None = None,
        title: str | None = UNSET,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> NoteData:
        """更新属性 / 正文并落盘记版本。"""
        merged = data.props()
        if props:
            merged.update(props)
        if title is not UNSET:
            data.title = title
        if tags is not None:
            data.tags = tags
        data.attrs["props"] = merged
        if text is not None:
            data.set_text(text)
        self.save(data, search_text=_search_text(data.title, data.text))
        return data

    @action
    def link(self, data: NoteData, target: Oid | str, relation: str = "references") -> Any:
        """从本笔记向目标建一条关系。"""
        from ..relation import Relation  # noqa: PLC0415 — 延迟导入，避免领域间加载期环

        return Relation.create(self.vault, data.oid, target, relation=relation, domain="note")

    @action
    def add_canvas(self, data: NoteData, canvas: CanvasData) -> str:
        """把一块画板嵌进正文：``canvas`` 追加其 oid，并在 body 末尾放占位。"""
        entry = str(canvas.oid)
        data.canvas = [*data.canvas, entry]
        data._append_marker(canvas_ref(len(data.canvas) - 1))  # noqa: SLF001
        self.save(data)
        return entry

    @action
    def add_access(
        self,
        data: NoteData,
        oid: Oid | str,
        *,
        mime: str = "",
        name: str = "",
        size: float = 0.0,
    ) -> str:
        """把一段外联资源嵌进正文：``access`` 追加 asset 的 oid，body 末尾放占位。

        资源本体与其元数据都在 ``Asset`` 块里，这里只存引用。
        """
        del mime, name, size
        entry = str(oid)
        data.access = [*data.access, entry]
        data._append_marker(access_ref(len(data.access) - 1))  # noqa: SLF001
        self.save(data)
        return entry


def _search_text(title: str | None, text: str) -> str:
    return f"{title or ''}\n{text}"


__all__ = [
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "CanvasBody",
    "CanvasData",
    "Form",
    "Graphic",
    "Line",
    "LineDict",
    "Link",
    "Note",
    "NoteBody",
    "NoteData",
    "Paint",
    "Segment",
    "Style",
    "StyleMap",
    "access_ref",
    "canvas_ref",
    "is_marker",
]
