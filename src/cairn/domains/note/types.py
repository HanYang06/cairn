# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记领域的数据结构与工具（收敛点）。

note 的类型本身在这里描述；``note/__init__.py`` 只做转出。

正文是 **list**，元素是「文字段」或「画板占位」；样式与之等长对齐：

    body   = ["床前明月光，", "疑是地上霜。", {"canvas": 0}, "低头思故乡"]
    style  = [Style(), Style(bold=True), Style(), Style()]
    canvas = [Canvas.to_data(), ...]        # 画板

画板里：
    - 图形（Graphic）承载几何：预制编号 + 中心点 + 尺寸 + 缩放 + 旋转 + 坐标；
    - 连线（Link）只记两端图形的**下标**与线型——走线是派生的，不存。

图形与连线都序列化成纯数值序列，文件里没有对象、没有文字。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any, ClassVar, Self

from ...core.store import Attr, Block, Body
from ...types import Oid
from ..base import UNSET

NOTE_KIND = "cairn.note"
NOTE_MIME = "application/x-cairn-note"
NOTE_SCHEMA = 1

Text = str
Segment = Text | dict[str, Any]


class Form(IntEnum):
    """预制图形编号（平面图形就这么多，从零画是不需要的）。"""

    CIRCLE = 0
    ELLIPSE = 1
    POLYGON = 2
    TRAPEZOID = 3
    PARALLELOGRAM = 4
    ARROW = 5


class Line(IntEnum):
    """线条分型，不预制。"""

    STRAIGHT = 0
    CURVE = 1
    ARROW = 2
    DASHED = 3


@dataclass(slots=True)
class Style:
    """一段文字的样式；全默认即"无修饰"。"""

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    font: str = ""
    color: str = ""
    size: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Style:
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)


@dataclass(slots=True)
class Paint:
    """图形的画法：描边 + 填充 + 渐变 + 透明度 + 闭合。

    颜色用 32 位整数 ``0xRRGGBBAA``（纯数字，落盘友好）；``0`` 表示不画。
    """

    stroke: int = 0
    width: float = 0.0
    line: int = 0                 # 线型（Line）
    fill: int = 0
    fill2: int = 0                # 渐变第二色；与 fill 相同即纯色
    grad: float = 0.0             # 渐变角度（度）
    alpha: float = 1.0            # 透明度 0..1
    closed: bool = False          # 是否闭合（填充需要）

    def to_seq(self) -> list[float]:
        return [
            float(self.stroke),
            self.width,
            float(self.line),
            float(self.fill),
            float(self.fill2),
            self.grad,
            self.alpha,
            1.0 if self.closed else 0.0,
        ]

    @classmethod
    def from_seq(cls, seq: Sequence[float]) -> Paint:
        values = [float(value) for value in seq]
        if len(values) < 8:
            return cls()
        return cls(
            stroke=int(values[0]),
            width=values[1],
            line=int(values[2]),
            fill=int(values[3]),
            fill2=int(values[4]),
            grad=values[5],
            alpha=values[6],
            closed=bool(values[7]),
        )


@dataclass(slots=True)
class Graphic:
    """一个图形 = 一条**点路径** + 变换 + 画法；渲染器只认点，不认形状。

    坐标约定：
        points   扁平点序列（x0,y0,x1,y1,…），**渲染真源**（乌龟画图那种）
        cx / cy  中心点（由最远边界算出，作为绘制的真实坐标）
        w / h    四方向最远边界推出的宽 / 高（点已按它归一化）
        scale    缩放：0 = 原始；负 = 缩小；正 = 放大（factor = 1 + scale）
        rot      旋转，正负
        paint    画法：描边 / 填充 / 渐变 / 透明度 / 闭合
        form     来源的预制编号；``-1`` 表示自定义，仅作记录，不参与渲染
        params   生成时用的外置参数，同样只是来源记录
    """

    form: int = -1
    cx: float = 0.0
    cy: float = 0.0
    w: float = 0.0
    h: float = 0.0
    rot: float = 0.0
    scale: float = 0.0
    points: list[float] = field(default_factory=list)
    params: list[float] = field(default_factory=list)
    paint: Paint = field(default_factory=Paint)

    def to_seq(self) -> list[float]:
        return [
            float(self.form),
            self.cx,
            self.cy,
            self.w,
            self.h,
            self.rot,
            self.scale,
            float(len(self.points)),
            *self.points,
            float(len(self.params)),
            *self.params,
            *self.paint.to_seq(),
        ]

    @classmethod
    def from_seq(cls, seq: Sequence[float]) -> Graphic:
        values = [float(value) for value in seq]
        if len(values) < 9:
            raise ValueError("图形序列过短")
        form, cx, cy, w, h, rot, scale = values[:7]
        point_count = int(values[7])
        points = values[8 : 8 + point_count]
        param_count = int(values[8 + point_count])
        params = values[9 + point_count : 9 + point_count + param_count]
        paint = Paint.from_seq(values[9 + point_count + param_count :])
        return cls(int(form), cx, cy, w, h, rot, scale, points, params, paint)


@dataclass(slots=True)
class Link:
    """两个图形之间的连线：只记下标与线型，走线派生。"""

    src: int = 0
    dst: int = 0
    kind: int = 0

    def to_seq(self) -> list[float]:
        return [float(self.src), float(self.dst), float(self.kind)]

    @classmethod
    def from_seq(cls, seq: Sequence[float]) -> Link:
        values = [float(value) for value in seq]
        return cls(int(values[0]), int(values[1]), int(values[2]))


@dataclass(slots=True)
class Canvas:
    """画板：图形 + 图形之间的关系。"""

    graphics: list[Graphic] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)

    def to_data(self) -> dict[str, list[list[float]]]:
        return {
            "g": [graphic.to_seq() for graphic in self.graphics],
            "l": [link.to_seq() for link in self.links],
        }

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> Canvas:
        return cls(
            graphics=[Graphic.from_seq(seq) for seq in (data.get("g") or ())],
            links=[Link.from_seq(seq) for seq in (data.get("l") or ())],
        )


def bare(text: str) -> list[Segment]:
    """纯文本 → 单元素正文。"""
    return [text]


def canvas_ref(index: int) -> dict[str, int]:
    """正文里的画板占位：指向 ``canvas`` 列表的第 ``index`` 块。"""
    return {"canvas": index}


def blank_styles(count: int) -> list[Style]:
    """生成 ``count`` 个空样式，与正文等长。"""
    return [Style() for _ in range(count)]


def normalize(
    body: list[Segment],
    style: list[Style] | None = None,
) -> tuple[list[Segment], list[Style]]:
    """规范化并对齐：丢弃空文字，``style`` 与 ``body`` 等长（缺的补空样式）。

    画板占位（dict）照原样保留。保证 ``len(body) == len(style)``。
    """
    styles = list(style or [])
    segments: list[tuple[Segment, Style]] = []
    for index, segment in enumerate(body):
        if segment == "":
            continue
        item = styles[index] if index < len(styles) else None
        segments.append((segment, item if isinstance(item, Style) else Style()))
    if not segments:
        return [""], [Style()]
    return [segment for segment, _ in segments], [entry for _, entry in segments]


class Note(Block):
    """笔记块：正文 + 画板 + 一大堆属性。"""

    type = NOTE_KIND
    mime: ClassVar[str | None] = NOTE_MIME
    body = Body(factory=list)

    # 内容相关
    style = Attr(factory=list)
    canvas = Attr(factory=list)             # 画板数据（Canvas.to_data() 列表）

    # 属性（正文之外，全在这里）
    schema = Attr(default=NOTE_SCHEMA)
    signature = Attr(default="")            # 创作签名
    privacy = Attr(default="")              # 隐私状态
    derived = Attr(factory=list)            # 派生关系列表
    authors = Attr(factory=list)            # 署名作者（有序：一作、二作…）；author 是原作者
    favorite = Attr(default=False)
    archived = Attr(default=False)
    trashed = Attr(default=False)
    share = Attr(factory=list)

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
        return "".join(segment for segment in self.body if isinstance(segment, str))

    def set_text(self, text: str) -> None:
        body, styles = normalize([text])
        self.body = body
        self.attrs["style"] = [style.to_dict() for style in styles]

    def reorder(self, order: Sequence[int]) -> None:
        """按旧下标顺序重排正文；样式跟着走，保持一一对齐。

        ``order`` 是旧索引的新排列，例如 ``[2, 0, 1]`` 把第 2 段提到最前。
        """
        body = list(self.body)
        styles = list(self.attrs.get("style") or ())
        self.body = [body[index] for index in order]
        self.attrs["style"] = [
            styles[index] if index < len(styles) else {} for index in order
        ]

    # ---- 画板 ----
    @property
    def canvases(self) -> list[Canvas]:
        """画板对象视图；落盘是紧凑数值数据（``canvas``）。"""
        return [Canvas.from_data(data) for data in (self.attrs.get("canvas") or ())]

    def set_canvases(self, items: Iterable[Canvas]) -> None:
        self.attrs["canvas"] = [canvas.to_data() for canvas in items]

    # ---- 引用 / 嵌入 ----
    @property
    def embeds(self) -> list[dict[str, Any]]:
        return [dict(item) for item in (self.attrs.get("embeds") or ())]

    @property
    def references(self) -> tuple[Oid, ...]:
        return tuple(Oid.parse(str(item["oid"])) for item in self.embeds if "oid" in item)

    def add_embed(
        self,
        oid: Oid | str,
        *,
        role: str = "embed",
        caption: str | None = None,
    ) -> Self:
        items = self.embeds
        entry: dict[str, Any] = {"oid": str(oid), "role": role}
        if caption is not None:
            entry["caption"] = str(caption)
        items.append(entry)
        self.attrs["embeds"] = items
        self.save()
        return self

    def link(self, target: Oid | str, relation: str = "references") -> Any:
        from ..relation import Relation

        return Relation.create(self._require_vault(), self.oid, target, relation=relation)

    # ---- 更新 ----
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


def _search_text(title: str | None, text: str) -> str:
    return f"{title or ''}\n{text}"


__all__ = [
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "Canvas",
    "Form",
    "Graphic",
    "Line",
    "Link",
    "Note",
    "Paint",
    "Segment",
    "Style",
    "bare",
    "blank_styles",
    "canvas_ref",
    "normalize",
]
