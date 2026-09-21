# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from feature.note import NoteData, Style
from feature.note.edit.style import line_styles
from feature.note.tools import (
    BASE_SIZE,
    PRESET_LAYOUT,
    TOOLS,
    ToolCategory,
    ToolContext,
    run_tool,
    tool_info,
)


def _note(text: str = "abcdef") -> NoteData:
    note = NoteData()
    note.body = [text]
    return note


def _ctx(note: NoteData, start: int = 0, end: int = 0) -> ToolContext:
    line = note.body[0]  # type: ignore[index]
    return ToolContext(
        line_id=line["id"],
        start=start,
        end=end,
        length=len(str(line["v"])),
        paragraph=note.paragraph(line["id"]),
    )


def test_toggle_bold_over_selection() -> None:
    note = _note()
    assert run_tool("bold", note, _ctx(note, 1, 3))
    assert line_styles(note.style, note.body[0]) == [(1, 3, Style(bold=True))]

    assert run_tool("bold", note, _ctx(note, 1, 3))
    assert line_styles(note.style, note.body[0]) == []


def test_toggle_without_selection_hits_whole_line() -> None:
    note = _note()
    run_tool("italic", note, _ctx(note))
    assert line_styles(note.style, note.body[0]) == [(0, 6, Style(italic=True))]


def test_align_toggle() -> None:
    note = _note()
    lid = note.body[0]["id"]  # type: ignore[index]

    run_tool("align-center", note, _ctx(note))
    assert note.paragraph(lid) == {"align": "center"}

    run_tool("align-center", note, _ctx(note))
    assert note.paragraph(lid) == {}


def test_heading_and_body() -> None:
    note = _note()
    lid = note.body[0]["id"]  # type: ignore[index]

    run_tool("h1", note, _ctx(note))
    assert note.paragraph(lid) == {"heading": 1}

    run_tool("body", note, _ctx(note))
    assert note.paragraph(lid) == {}


def test_indent_in_and_out() -> None:
    note = _note()
    lid = note.body[0]["id"]  # type: ignore[index]

    run_tool("indent-in", note, _ctx(note))
    run_tool("indent-in", note, _ctx(note))
    assert note.paragraph(lid) == {"level": 2}

    run_tool("indent-out", note, _ctx(note))
    run_tool("indent-out", note, _ctx(note))
    assert note.paragraph(lid) == {}


def test_size_up_and_back_to_default() -> None:
    note = _note()
    run_tool("size-up", note, _ctx(note))
    assert line_styles(note.style, note.body[0]) == [(0, 6, Style(size=BASE_SIZE + 1))]

    run_tool("size-down", note, _ctx(note))
    assert line_styles(note.style, note.body[0]) == []


def test_clear_format() -> None:
    note = _note()
    run_tool("bold", note, _ctx(note))
    run_tool("clear-format", note, _ctx(note))
    assert line_styles(note.style, note.body[0]) == []


def test_registry_and_preset_are_consistent() -> None:
    ids = [tid for row in PRESET_LAYOUT for group in row for tid in group]
    assert ids
    assert all(tid in TOOLS for tid in ids)
    assert all(info["id"] and info["label"] for info in tool_info())


def test_unknown_tool_returns_false() -> None:
    note = _note()
    assert run_tool("does-not-exist", note, _ctx(note)) is False


def test_tool_categories_and_availability() -> None:
    assert TOOLS["bold"].category == ToolCategory.EDIT
    assert TOOLS["insert-code"].category == ToolCategory.ADD
    info = {tool["id"]: tool for tool in tool_info()}
    assert info["bold"]["category"] == "edit"
    assert info["bold"]["available"] is True
    assert info["insert-table"]["available"] is False


def test_placeholder_tool_does_not_run() -> None:
    note = _note()
    assert run_tool("insert-table", note, _ctx(note)) is False
    assert len(note.blocks()) == 1


def test_toggle_state_three_way() -> None:
    note = _note("abcd")
    run_tool("bold", note, _ctx(note, 0, 2))

    assert TOOLS["bold"].state(note, _ctx(note, 0, 2)) is True
    assert TOOLS["bold"].state(note, _ctx(note, 2, 4)) is False
    assert TOOLS["bold"].state(note, _ctx(note)) is None


def test_paragraph_tool_state() -> None:
    note = _note()
    assert TOOLS["align-center"].state(note, _ctx(note)) is False

    run_tool("align-center", note, _ctx(note))
    assert TOOLS["align-center"].state(note, _ctx(note)) is True
    assert TOOLS["h1"].state(note, _ctx(note)) is False


def test_insert_code_tool_sets_focus_and_paragraph() -> None:
    note = _note("x")
    ctx = _ctx(note)
    assert run_tool("insert-code", note, ctx)
    assert ctx.focus

    blocks = note.blocks()
    assert len(blocks) == 2
    assert blocks[1]["id"] == ctx.focus
    assert blocks[1]["para"] == {"block": "code"}
