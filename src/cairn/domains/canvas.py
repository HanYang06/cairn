# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""画板：**全局内容类型**（`cairn.canvas` 块，与 note / asset 同级，任何领域都能引用）。

- 数据（``CanvasBody``）：``mode``（diagram 逻辑图 / sketch 自由手绘）+ 图形 + 连线。
  图形 = 点路径 + 变换 + 画法（数值序列）；连线只记下标 + 线型，走线派生。
- 身份：作为块有 ``id`` / ``oid``，内容寻址、全局去重；笔记用 oid 引用它。

这里也定义渲染用的基础值对象：``Form`` / ``Line`` / ``Paint`` / ``Graphic`` / ``Link``。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING, Any

from ..core.store import Block, Body

if TYPE_CHECKING:
    from collections.abc import Sequence

CANVAS_KIND = "cairn.canvas"
CANVAS_MODE = ("diagram", "sketch")


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


class CanvasBody(Body):
    """画板内容：``mode`` + 图形 + 连线（全是数值）。"""

    def __init__(
        self,
        mode: str = "diagram",
        graphics: Sequence[Graphic] | None = None,
        links: Sequence[Link] | None = None,
        hash: str = "",
    ) -> None:
        self.mode = str(mode)
        self.graphics = list(graphics or ())
        self.links = list(links or ())
        self.hash = str(hash or "")
        if not self.hash:
            self.refresh()

    def content(self) -> dict[str, Any]:
        return {
            "m": self.mode,
            "g": [graphic.to_seq() for graphic in self.graphics],
            "l": [link.to_seq() for link in self.links],
        }

    def to_data(self) -> dict[str, Any]:
        return {**self.content(), "hash": self.hash}

    @classmethod
    def from_data(cls, data: Any) -> CanvasBody:
        if not data:
            return cls()
        return cls(
            mode=str(data.get("m") or "diagram"),
            graphics=[Graphic.from_seq(seq) for seq in (data.get("g") or ())],
            links=[Link.from_seq(seq) for seq in (data.get("l") or ())],
            hash=str(data.get("hash") or ""),
        )

    def refresh(self) -> CanvasBody:
        super().refresh()
        return self


class Canvas(Block):
    """画板块：``body = CanvasBody``；内容寻址、全局引用。"""

    type = CANVAS_KIND

    body: CanvasBody = CanvasBody()

    def __init__(self, **kwargs: Any) -> None:
        graphics = kwargs.pop("graphics", None)
        links = kwargs.pop("links", None)
        mode = kwargs.pop("mode", "diagram")
        super().__init__(**kwargs)
        if graphics is not None or links is not None or "body" not in kwargs:
            self.body = CanvasBody(mode=mode, graphics=graphics, links=links)

    @classmethod
    def create(
        cls,
        vault: Any,
        *,
        graphics: Sequence[Graphic] | None = None,
        links: Sequence[Link] | None = None,
        mode: str = "diagram",
    ) -> Canvas:
        canvas = cls(graphics=graphics, links=links, mode=mode)
        canvas._vault = vault
        canvas.save()
        return canvas

    @property
    def mode(self) -> str:
        return self.body.mode

    @property
    def graphics(self) -> list[Graphic]:
        return self.body.graphics

    @property
    def links(self) -> list[Link]:
        return self.body.links


__all__ = [
    "CANVAS_KIND",
    "CANVAS_MODE",
    "Canvas",
    "CanvasBody",
    "Form",
    "Graphic",
    "Line",
    "Link",
    "Paint",
]
