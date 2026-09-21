# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""外置图形集：读 ``config/shapes.json``，提供预制图形与其外置参数。

两件事：
  1. UI——``ShapeSet.for_ui()`` 直接给界面用（名字 / 说明 / 参数表）；
  2. 生成——``build_vertices()`` 按编号取生成器，算出归一化后的顶点。

图形学部分（归一化、顶点生成）在这里；数据/参数在 JSON 里，改图不改代码。

状态：草案 v1（基础图形；复杂图形待补）。
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHAPE_SET_ENV = "CAIRN_SHAPES"
_SHAPE_SET_REL = Path("config") / "shapes.json"


@dataclass(frozen=True, slots=True)
class Param:
    """一个外置参数（UI 可编辑，生成器使用）。"""

    key: str
    name: str
    type: str = "float"
    default: Any = None
    min: float | None = None
    max: float | None = None


@dataclass(frozen=True, slots=True)
class ShapeSpec:
    """一个预制图形的定义。"""

    id: int
    key: str
    name: str
    desc: str
    gen: str
    params: tuple[Param, ...] = ()

    def defaults(self) -> dict[str, Any]:
        return {param.key: param.default for param in self.params}


@dataclass(frozen=True, slots=True)
class ShapeSet:
    """整套图形集。"""

    version: int
    name: str
    shapes: tuple[ShapeSpec, ...] = ()
    lines: tuple[ShapeSpec, ...] = ()

    def get(self, form_id: int) -> ShapeSpec | None:
        for spec in (*self.shapes, *self.lines):
            if spec.id == form_id:
                return spec
        return None

    def by_key(self, key: str) -> ShapeSpec | None:
        for spec in (*self.shapes, *self.lines):
            if spec.key == key:
                return spec
        return None

    def for_ui(self) -> list[dict[str, Any]]:
        """给界面的扁平列表：名字 / 说明 / 参数。"""
        return [
            {
                "id": spec.id,
                "key": spec.key,
                "name": spec.name,
                "desc": spec.desc,
                "params": [
                    {
                        "key": param.key,
                        "name": param.name,
                        "type": param.type,
                        "default": param.default,
                        "min": param.min,
                        "max": param.max,
                    }
                    for param in spec.params
                ],
            }
            for spec in self.shapes
        ]


def repo_root() -> Path:
    """从本文件向上找到含 ``pyproject.toml`` 的目录。"""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[3]


def shape_set_path() -> Path:
    """形状集文件路径：``SHAPE_SET_ENV`` 覆盖，否则用仓库内默认位置。"""
    override = os.environ.get(SHAPE_SET_ENV)
    if override:
        return Path(override)
    return repo_root() / _SHAPE_SET_REL


def _param(raw: dict[str, Any]) -> Param:
    return Param(
        key=str(raw["key"]),
        name=str(raw.get("name", raw["key"])),
        type=str(raw.get("type", "float")),
        default=raw.get("default"),
        min=raw.get("min"),
        max=raw.get("max"),
    )


def _spec(raw: dict[str, Any]) -> ShapeSpec:
    return ShapeSpec(
        id=int(raw["id"]),
        key=str(raw["key"]),
        name=str(raw.get("name", raw["key"])),
        desc=str(raw.get("desc", "")),
        gen=str(raw.get("gen", raw["key"])),
        params=tuple(_param(item) for item in (raw.get("params") or ())),
    )


def load_shape_set(path: Path | str | None = None) -> ShapeSet:
    """读取图形集；默认从 ``config/shapes.json``（可用 ``CAIRN_SHAPES`` 覆盖）。"""
    target = Path(path) if path is not None else shape_set_path()
    data = json.loads(target.read_text(encoding="utf-8"))
    return ShapeSet(
        version=int(data.get("version", 1)),
        name=str(data.get("name", "shapes")),
        shapes=tuple(_spec(item) for item in (data.get("shapes") or ())),
        lines=tuple(_spec(item) for item in (data.get("lines") or ())),
    )


# ---- 生成器：把参数变成归一化顶点（中心在 0,0）----


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _flatten(points: Any) -> list[float]:
    return [float(coord) for point in points for coord in point]


def _sample_ellipse(rx: float, ry: float, count: int = 64) -> list[float]:
    return _flatten(
        (
            rx * math.cos(2 * math.pi * index / count),
            ry * math.sin(2 * math.pi * index / count),
        )
        for index in range(count)
    )


def _circle(w: float, h: float, _params: dict[str, Any]) -> list[float]:
    radius = min(w, h) / 2
    return _sample_ellipse(radius, radius)


def _ellipse(w: float, h: float, _params: dict[str, Any]) -> list[float]:
    return _sample_ellipse(w / 2, h / 2)


def _polygon(w: float, h: float, params: dict[str, Any]) -> list[float]:
    sides = max(3, int(params.get("sides", 6)))
    radius = min(w, h) / 2
    return _flatten(
        (
            radius * math.cos(-math.pi / 2 + 2 * math.pi * index / sides),
            radius * math.sin(-math.pi / 2 + 2 * math.pi * index / sides),
        )
        for index in range(sides)
    )


def _trapezoid(w: float, h: float, params: dict[str, Any]) -> list[float]:
    top = _clamp(float(params.get("top", 0.5)), 0.0, 1.0)
    hw, hh = w / 2, h / 2
    return _flatten([(-hw, -hh), (hw, -hh), (top * hw, hh), (-top * hw, hh)])


def _parallelogram(w: float, h: float, params: dict[str, Any]) -> list[float]:
    slant = _clamp(float(params.get("slant", 0.5)), -0.9, 0.9)
    hw, hh = w / 2, h / 2
    dx = slant * hw
    return _flatten([(-hw, -hh), (hw, -hh), (hw - dx, hh), (-hw - dx, hh)])


def _arrow(w: float, h: float, params: dict[str, Any]) -> list[float]:
    head = _clamp(float(params.get("head", 0.4)), 0.1, 0.9)
    tail = _clamp(float(params.get("tail", 0.5)), 0.05, 1.0)
    hw, hh = w / 2, h / 2
    half_tail = hh * tail
    head_x = hw - head * w
    return _flatten(
        [
            (-hw, -half_tail),
            (head_x, -half_tail),
            (head_x, -hh),
            (hw, 0.0),
            (head_x, hh),
            (head_x, half_tail),
            (-hw, half_tail),
        ]
    )


_GENERATORS = {
    "circle": _circle,
    "ellipse": _ellipse,
    "polygon": _polygon,
    "trapezoid": _trapezoid,
    "parallelogram": _parallelogram,
    "arrow": _arrow,
}


def build_vertices(
    spec: ShapeSpec,
    *,
    w: float,
    h: float,
    params: dict[str, Any] | None = None,
) -> list[float]:
    """按图形定义算出顶点（扁平 x,y 序列，中心在 0,0）。"""
    values = spec.defaults()
    if params:
        values.update(params)
    generator = _GENERATORS.get(spec.gen)
    if generator is None:
        raise ValueError(f"未知生成器: {spec.gen}")
    return generator(w, h, values)


def graphic_from(  # noqa: PLR0913 — 生成入口：几何参数均有默认值
    spec: ShapeSpec,
    *,
    cx: float = 0.0,
    cy: float = 0.0,
    w: float = 1.0,
    h: float = 1.0,
    params: dict[str, Any] | None = None,
) -> Any:
    """由预制图形生成一个 ``Graphic``：点已算好，``form`` / ``params`` 只留作来源记录。"""
    from .model import Graphic  # noqa: PLC0415 — 延迟导入，避免与 model 的加载期环

    values = spec.defaults()
    if params:
        values.update(params)
    points = build_vertices(spec, w=w, h=h, params=values)
    ordered = [float(values.get(param.key, 0.0) or 0.0) for param in spec.params]
    return Graphic(
        form=spec.id,
        cx=cx,
        cy=cy,
        w=w,
        h=h,
        points=points,
        params=ordered,
    )


__all__ = [
    "SHAPE_SET_ENV",
    "Param",
    "ShapeSet",
    "ShapeSpec",
    "build_vertices",
    "graphic_from",
    "load_shape_set",
    "repo_root",
    "shape_set_path",
]
