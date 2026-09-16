# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记的**纯数据模型**：样式、画板、图形、连线、嵌入引用。

这一层不依赖库、不依赖引擎，只是可序列化的值对象；供 ``edit`` / ``versions`` /
``types`` 共用，避免循环依赖。

坐标 / 序列化约定见 ``types.py`` 顶部的说明（正文 = 行序列 + 行内区间样式）。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from enum import IntEnum
from typing import Any

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
    """一段文字的样式；全默认即"无修饰"。

    段级 / 行内区间共用同一个结构；行内样式由 ``edit`` 的区间叠加表达。
    """

    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    font: str = ""
    color: str = ""
    size: float = 0.0

    def to_data(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> Style:
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)


@dataclass(slots=True)
class Paint:
    """图形的画法：描边 + 填充 + 渐变 + 透明度 + 闭合。

    颜色用 32 位整数 ``0xRRGGBBAA``（纯数字，落盘友好）；``0`` 表示不画。
    """

    stroke: int = 0
    width: float = 0.0
    line: int = 0
    fill: int = 0
    fill2: int = 0
    grad: float = 0.0
    alpha: float = 1.0
    closed: bool = False

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
    """一个图形 = 一条**点路径** + 变换 + 画法；渲染器只认点，不认形状。"""

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
class Access:
    """正文里嵌入的多媒体引用：真正的字节在资产（``Asset``）块里。"""

    oid: str = ""
    mime: str = ""
    name: str = ""
    size: float = 0.0

    def to_data(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> Access:
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)


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
    def from_data(cls, data: Mapping[str, Any]) -> Canvas:
        return cls(
            graphics=[Graphic.from_seq(seq) for seq in (data.get("g") or ())],
            links=[Link.from_seq(seq) for seq in (data.get("l") or ())],
        )


__all__ = [
    "NOTE_KIND",
    "NOTE_MIME",
    "NOTE_SCHEMA",
    "Access",
    "Canvas",
    "Form",
    "Graphic",
    "Line",
    "Link",
    "Paint",
    "Segment",
    "Style",
    "Text",
]
