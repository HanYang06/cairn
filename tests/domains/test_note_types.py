# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from cairn.domains.note.types import (
    Access,
    Canvas,
    Form,
    Graphic,
    Line,
    Link,
    Note,
    Paint,
    Style,
    access_ref,
    bare,
    blank_styles,
    canvas_ref,
    normalize,
)
from cairn.types import Oid


def _graphic(**overrides: object) -> Graphic:
    values: dict[str, object] = {"form": Form.CIRCLE, "cx": 0.0, "cy": 0.0, "w": 2.0, "h": 2.0}
    values.update(overrides)
    return Graphic(**values)  # type: ignore[arg-type]


def test_bare_is_single_element() -> None:
    assert bare("床前明月光，低头思故乡") == ["床前明月光，低头思故乡"]


def test_blank_styles_are_aligned() -> None:
    assert blank_styles(3) == [Style(), Style(), Style()]


def test_normalize_drops_empty_and_aligns() -> None:
    body, style = normalize(["床前明月光，", "", "低头思故乡"], [Style(bold=True)])
    assert body == ["床前明月光，", "低头思故乡"]
    assert style == [Style(bold=True), Style()]


def test_normalize_keeps_embed_markers() -> None:
    body, style = normalize(["文字", canvas_ref(0), access_ref(1), "尾"])
    assert body == ["文字", {"canvas": 0}, {"access": 1}, "尾"]
    assert style == [Style(), Style(), Style(), Style()]


def test_normalize_empty() -> None:
    assert normalize([]) == ([""], [Style()])


def test_style_roundtrips_through_data() -> None:
    style = Style(bold=True, font="serif")
    assert Style.from_data(style.to_data()) == style


def test_graphic_serializes_to_numbers_and_back() -> None:
    graphic = Graphic(
        form=Form.PARALLELOGRAM,
        cx=1.5,
        cy=2.5,
        w=10.0,
        h=4.0,
        rot=0.5,
        scale=0.25,
        points=[0.0, 0.0, 1.0, 1.0],
        params=[3.0],
        paint=Paint(stroke=0xFF0000FF, width=2.0, fill=0x00FF00FF, grad=45.0, closed=True),
    )
    seq = graphic.to_seq()
    assert all(isinstance(value, float) for value in seq)
    assert Graphic.from_seq(seq) == graphic


def test_paint_serializes_to_numbers_and_back() -> None:
    paint = Paint(stroke=0x12345678, width=1.5, line=Line.DASHED, fill=0xABCDEF00,
                  fill2=0x00ABCDEF, grad=90.0, alpha=0.5, closed=True)
    seq = paint.to_seq()
    assert all(isinstance(value, float) for value in seq)
    assert Paint.from_seq(seq) == paint


def test_canvas_roundtrips_graphics_and_links() -> None:
    canvas = Canvas(
        graphics=[_graphic(), _graphic(form=Form.POLYGON, cx=5.0)],
        links=[Link(src=0, dst=1, kind=Line.CURVE)],
    )
    data = canvas.to_data()
    assert all(isinstance(seq, list) for seq in data["g"])
    assert data["l"] == [[0.0, 1.0, float(Line.CURVE)]]
    assert Canvas.from_data(data) == canvas


def test_note_typed_canvas_and_marker() -> None:
    note = Note()
    note.body = ["床前明月光，", canvas_ref(0), "低头思故乡"]
    note.canvas = [Canvas(graphics=[_graphic()])]

    assert note.body[1] == {"canvas": 0}
    assert note.text == "床前明月光，低头思故乡"
    assert isinstance(note.canvas[0], Canvas)          # 取出来是对象，不是 dict
    assert note.canvas[0].graphics == [_graphic()]


def test_note_typed_access_and_marker() -> None:
    oid = str(Oid.new())
    note = Note()
    note.body = ["图：", access_ref(0)]
    note.access = [Access(oid=oid, mime="image/png", name="a.png", size=3.0)]

    assert note.body[1] == {"access": 0}
    assert isinstance(note.access[0], Access)
    assert note.access[0].mime == "image/png"
    assert note.references == (note.access[0].oid,)


def test_add_access_embeds_into_body() -> None:
    note = Note()
    note.body = ["看图"]
    note.style = [Style()]
    note.access = []
    entry = note.add_access(str(Oid.new()), mime="video/mp4", name="clip.mp4")
    assert entry.mime == "video/mp4"
    assert note.body[-1] == {"access": 0}
    assert note.access[0] == entry


def test_reorder_keeps_body_and_style_aligned() -> None:
    note = Note()
    note.body = ["a", "b", "c"]
    note.style = [Style(bold=True), Style(), Style(italic=True)]

    note.reorder([2, 0, 1])

    assert note.body == ["c", "a", "b"]
    assert note.style == [Style(italic=True), Style(bold=True), Style()]


def test_set_text_preserves_markers() -> None:
    note = Note()
    note.body = ["前面", {"access": 0}, "后面"]
    note.style = [Style(), Style(), Style()]
    note.access = [Access(oid=str(Oid.new()), mime="image/png")]

    note.set_text("前面后面改")

    assert note.body == ["前面", {"access": 0}, "后面改"]


def test_set_text_keeps_boundary_marker_drops_inner() -> None:
    note = Note()
    note.body = ["前面", {"access": 0}, "后面"]
    note.style = [Style(), Style(), Style()]
    note.access = [Access(oid=str(Oid.new()), mime="image/png")]
    note.set_text("前面后面改")          # 占位在边界 → 保留
    assert note.body == ["前面", {"access": 0}, "后面改"]

    inner = Note()
    inner.body = ["abc", {"canvas": 0}, "def"]
    inner.canvas = [Canvas()]
    inner.set_text("abXYZ")             # 占位落在被替换区间内 → 消失
    assert inner.body == ["abXYZ"]
