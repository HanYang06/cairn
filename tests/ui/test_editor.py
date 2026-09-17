# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""富文本编辑器测试：文档往返 + 编辑器意图 + App 落盘。"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtGui import QTextCursor

from cairn.core import Vault
from cairn.domains import Note
from cairn.domains.note.types import Style
from cairn.ui.editor import NoteDocument, NoteEditor
from cairn.ui.root import App

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.usefixtures("qapp")


def _note_with_body(tmp_path: Path) -> tuple[Note, Vault]:
    vault = Vault.create(tmp_path / "vault")
    note = Note.create(vault, "第一行")
    note.set_body(
        [
            {"id": "L1", "v": "标题", "p": {"heading": 1, "align": "center"}},
            {"id": "L2", "v": "正文加粗"},
            {"id": "L3", "v": {"access": 0}},
        ],
        style={"L2": [{(0, 2): Style(bold=True)}]},
    )
    return note, vault


def test_note_document_roundtrip(tmp_path: Path) -> None:
    note, _ = _note_with_body(tmp_path)
    document = NoteDocument()
    document.load_note(note)
    body, style = document.to_body()

    assert [line["id"] for line in body] == ["L1", "L2", "L3"]
    assert body[0]["v"] == "标题"
    assert body[0]["p"]["heading"] == 1
    assert body[0]["p"]["align"] == "center"
    assert body[2]["v"] == {"access": 0}
    assert style["L2"][0][(0, 2)].bold is True


def test_editor_emits_body_changed(tmp_path: Path) -> None:
    note, _ = _note_with_body(tmp_path)
    editor = NoteEditor()
    seen: list[tuple[list[dict], dict]] = []
    editor.body_changed.connect(lambda body, style: seen.append((body, style)))

    editor.load_note(note)
    cursor = editor.edit.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.Start)
    editor.edit.setTextCursor(cursor)
    editor.edit.insertPlainText("XYZ")

    assert seen
    body, _style = seen[-1]
    assert body[0]["v"].startswith("XYZ")


def test_app_update_body_persists(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    note = Note.create(vault, "一")
    root = App(vault)
    root.open_note(str(note.oid))

    root.update_current_body([{"id": "x", "v": "改了"}], {})
    root.flush_body()

    reloaded = Note.load(vault, note.oid)
    assert reloaded.text == "改了"
    root.shutdown()
