# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from feature.note import Form, Line
from feature.note.shapes import Param, ShapeSpec, build_vertices, graphic_from, load_shape_set


def test_load_shape_set() -> None:
    shapes = load_shape_set()
    assert shapes.version == 1
    keys = {spec.key for spec in shapes.shapes}
    assert {"circle", "ellipse", "polygon", "trapezoid", "parallelogram", "arrow"} <= keys


def test_ids_match_enums() -> None:
    shapes = load_shape_set()
    assert {spec.id for spec in shapes.shapes} == {int(form) for form in Form}
    assert {spec.id for spec in shapes.lines} == {int(line) for line in Line}


def test_for_ui_exposes_params() -> None:
    ui = {item["key"]: item for item in load_shape_set().for_ui()}
    assert ui["polygon"]["name"] == "正多边形"
    assert ui["polygon"]["params"][0]["key"] == "sides"
    assert ui["polygon"]["params"][0]["default"] == 6


def test_by_key_and_defaults() -> None:
    spec = load_shape_set().by_key("parallelogram")
    assert spec is not None
    assert spec.defaults() == {"slant": 0.5}


def test_defaults_skip_undeclared_params() -> None:
    spec = ShapeSpec(
        id=99,
        key="k",
        name="n",
        desc="",
        gen="polygon",
        params=(
            Param(key="a", name="a", type="float", default=None),
            Param(key="b", name="b", type="float", default=2.0),
        ),
    )
    assert spec.defaults() == {"b": 2.0}


def test_build_polygon_vertex_count() -> None:
    spec = load_shape_set().by_key("polygon")
    assert spec is not None
    points = build_vertices(spec, w=10.0, h=10.0, params={"sides": 4})
    assert len(points) == 8


def test_build_arrow_has_seven_points() -> None:
    spec = load_shape_set().by_key("arrow")
    assert spec is not None
    points = build_vertices(spec, w=10.0, h=10.0)
    assert len(points) == 14


def test_graphic_from_generates_points_and_keeps_provenance() -> None:
    spec = load_shape_set().by_key("polygon")
    assert spec is not None
    graphic = graphic_from(spec, cx=3.0, cy=-1.0, w=8.0, h=8.0, params={"sides": 3})
    assert graphic.form == int(Form.POLYGON)
    assert graphic.cx == 3.0
    assert len(graphic.points) == 6  # 三角形三个点
    assert graphic.params == [3.0]  # 来源参数（边数）
    assert graphic.to_seq()  # 可落盘


def test_invalid_spec_raises_with_context(tmp_path) -> None:
    path = tmp_path / "s.json"
    path.write_text('{"shapes": [{"id": 1}]}', encoding="utf-8")

    with pytest.raises(ValueError, match="图形定义非法"):
        load_shape_set(path)


def test_duplicate_ids_raise(tmp_path) -> None:
    path = tmp_path / "s.json"
    path.write_text(
        '{"shapes": [{"id": 1, "key": "a"}, {"id": 1, "key": "b"}]}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="重复"):
        load_shape_set(path)


def test_non_numeric_param_raises() -> None:
    spec = ShapeSpec(
        id=7,
        key="k",
        name="n",
        desc="",
        gen="polygon",
        params=(Param(key="unused", name="unused", type="float", default="many"),),
    )

    with pytest.raises(TypeError, match="不是数值"):
        graphic_from(spec, w=1.0, h=1.0)
