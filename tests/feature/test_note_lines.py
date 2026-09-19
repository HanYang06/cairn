# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from feature.note.edit import OVERLONG_WEIGHT, line_styles, text_weight
from feature.note.types import NoteData, Style, access_ref


def _texts(note: NoteData) -> list[str]:
    return [line["v"] for line in note.body]  # type: ignore[misc]


def _ids(note: NoteData) -> list[str]:
    return [line["id"] for line in note.body]  # type: ignore[misc]


def test_set_line_keeps_other_ids() -> None:
    note = NoteData()
    note.body = ["甲", "乙", "丙"]
    ids = _ids(note)

    note.set_line(ids[1], "乙改")

    assert _texts(note) == ["甲", "乙改", "丙"]
    assert _ids(note) == ids


def test_set_line_with_newline_splits_in_place() -> None:
    note = NoteData()
    note.body = ["前", "后"]
    ids = _ids(note)

    note.set_line(ids[0], "一\n二")

    assert _texts(note) == ["一", "二", "后"]
    assert note.body[2]["id"] == ids[1]  # type: ignore[index]


def test_insert_line_after_places_and_returns_id() -> None:
    note = NoteData()
    note.body = ["甲", "乙"]
    first = _ids(note)[0]

    new_id = note.insert_line_after(first, "插入")

    assert _texts(note) == ["甲", "插入", "乙"]
    assert note.body[1]["id"] == new_id  # type: ignore[index]


def test_remove_line_drops_text_and_style() -> None:
    note = NoteData()
    note.body = ["甲", "乙"]
    ids = _ids(note)
    note.toggle_style(ids[1], 0, 1, "bold")

    note.remove_line(ids[1])

    assert _texts(note) == ["甲"]
    assert ids[1] not in note.style


def test_remove_last_line_keeps_one_empty() -> None:
    note = NoteData()
    note.body = ["只有一行"]

    note.remove_line(_ids(note)[0])

    assert _texts(note) == [""]


def test_split_line_carries_style_to_right() -> None:
    note = NoteData()
    note.body = ["abcdef"]
    lid = _ids(note)[0]
    note.toggle_style(lid, 3, 6, "bold")

    note.split_line(lid, 3)

    assert _texts(note) == ["abc", "def"]
    right = line_styles(note.style, note.body[1])  # type: ignore[index]
    assert right == [(0, 3, Style(bold=True))]
    assert lid not in note.style


def test_merge_line_concatenates_and_shifts_style() -> None:
    note = NoteData()
    note.body = ["abc", "def"]
    ids = _ids(note)
    note.toggle_style(ids[1], 0, 3, "italic")

    merged_id = note.merge_line(ids[1])

    assert merged_id == ids[0]
    assert _texts(note) == ["abcdef"]
    merged = line_styles(note.style, note.body[0])
    assert merged == [(3, 6, Style(italic=True))]


def test_merge_first_line_is_noop() -> None:
    note = NoteData()
    note.body = ["abc", "def"]

    assert note.merge_line(_ids(note)[0]) is None
    assert _texts(note) == ["abc", "def"]


def test_merge_marker_line_is_noop() -> None:
    note = NoteData()
    note.body = ["abc", access_ref(0)]
    marker_id = _ids(note)[1]

    assert note.merge_line(marker_id) is None
    assert _texts(note)[0] == "abc"


def test_toggle_style_on_and_off() -> None:
    note = NoteData()
    note.body = ["abcdef"]
    lid = _ids(note)[0]

    note.toggle_style(lid, 1, 3, "bold")
    assert line_styles(note.style, note.body[0]) == [(1, 3, Style(bold=True))]

    note.toggle_style(lid, 1, 3, "bold")
    assert line_styles(note.style, note.body[0]) == []


def test_toggle_style_range_inside_existing() -> None:
    note = NoteData()
    note.body = ["abcdef"]
    lid = _ids(note)[0]
    note.toggle_style(lid, 0, 6, "bold")

    note.toggle_style(lid, 2, 4, "italic")

    assert line_styles(note.style, note.body[0]) == [
        (0, 2, Style(bold=True)),
        (2, 4, Style(bold=True, italic=True)),
        (4, 6, Style(bold=True)),
    ]


def test_toggle_style_updates_body_hash() -> None:
    note = NoteData()
    note.body = ["abcdef"]
    lid = _ids(note)[0]
    before = note.body.hash

    note.toggle_style(lid, 0, 3, "bold")

    assert note.body.hash != before


def test_paragraph_roundtrip_and_hash() -> None:
    left = NoteData()
    left.body = ["标题"]
    lid = _ids(left)[0]
    right = NoteData()
    right.body = ["标题"]

    left.set_paragraph(lid, {"heading": 1})

    assert left.paragraph(lid) == {"heading": 1}
    assert left.body.hash != right.body.hash


def test_set_paragraph_merges_and_deletes() -> None:
    note = NoteData()
    note.body = ["x"]
    lid = _ids(note)[0]

    note.set_paragraph(lid, {"align": "center", "heading": 2})
    note.set_paragraph(lid, {"heading": None})

    assert note.paragraph(lid) == {"align": "center"}

    note.clear_paragraph(lid)
    assert note.paragraph(lid) == {}


def test_split_and_merge_preserve_paragraph() -> None:
    note = NoteData()
    note.body = ["abcdef"]
    lid = _ids(note)[0]
    note.set_paragraph(lid, {"list": "bullet"})

    new_id = note.split_line(lid, 3)
    assert note.paragraph(lid) == {"list": "bullet"}
    assert note.paragraph(new_id) == {"list": "bullet"}

    note.merge_line(new_id)
    assert note.paragraph(lid) == {"list": "bullet"}


def test_blocks_expose_para_and_weight() -> None:
    note = NoteData()
    note.body = ["标题"]
    lid = _ids(note)[0]
    note.set_paragraph(lid, {"heading": 1})

    block = note.blocks()[0]
    assert block["para"] == {"heading": 1}
    assert block["weight"] == 2.0
    assert block["overlong"] is False


def test_overlong_flag_at_threshold() -> None:
    note = NoteData()
    note.body = ["字" * 301]
    assert note.blocks()[0]["overlong"] is True

    note.body = ["字" * 300]
    assert note.blocks()[0]["overlong"] is False


def test_text_weight_counts_wide_as_one() -> None:
    assert text_weight("你好") == 2.0
    assert text_weight("ab") == 1.0
    assert text_weight("a你") == 1.5
    assert OVERLONG_WEIGHT == 300.0
