# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Show`：最小数据单元的确定性归集 / 分组 / 默认呈现。"""

from __future__ import annotations

from feature import NoteData
from ui_tools.core import Show


def _note(text: str = "你好") -> NoteData:
    note = NoteData()
    note.body = [text, "世界"]
    note.title = "标题"
    note.tags = {"a": "1"}
    return note


def test_show_single_unit() -> None:
    note = _note()
    show = Show(note)

    assert show.title == "标题"
    assert show.attrs["title"] == "标题"
    assert show.ids[0] == str(note.id)
    assert set(show.ids) >= {line["id"] for line in note.body}
    assert show.body_kinds == ["lines"]
    assert show.groups["notedata"]


def test_show_merges_multiple_units() -> None:
    first = _note()
    second = _note()
    second.title = "第二"

    show = Show([first, second])

    assert len(show.parts) == 2
    assert show.title == "第二"  # 同名后写覆盖
    assert set(show.groups) == {"notedata"}
    assert len(show.ids) >= 6
    assert len(show.bodies) == 2


def test_show_field_kinds_are_deterministic() -> None:
    kinds = Show(_note()).parts[0].fields

    assert kinds["title"] == "text"
    assert kinds["favorite"] == "toggle"
    assert kinds["tags"] == "kv"


def test_show_accepts_set_input() -> None:
    first = _note()
    second = _note()
    second.title = "第二"

    show = Show({first, second})

    assert len(show.parts) == 2


def test_show_set_input_is_ordered_deterministically() -> None:
    low = NoteData(id="00000000000000000000000001")
    low.body = ["a"]
    high = NoteData(id="00000000000000000000000002")
    high.body = ["b"]

    show = Show({high, low})

    assert show.parts[0].ids[0] == "00000000000000000000000001"


def test_show_dedupes_groups_and_ids() -> None:
    note = _note()

    show = Show([note, note])

    assert len(show.ids) == len(set(show.ids))
    assert len(show.groups["notedata"]) == len(set(show.groups["notedata"]))
