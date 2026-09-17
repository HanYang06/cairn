# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Session` 投影缓存与变更信号测试（Qt-free）。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cairn.core import Vault
from cairn.domains import Note
from cairn.ui.session import Session

if TYPE_CHECKING:
    from pathlib import Path


def _session(tmp_path: Path) -> tuple[Session, Vault]:
    vault = Vault.create(tmp_path / "vault")
    return Session(vault), vault


def test_note_rows_empty_then_reflect_create(tmp_path: Path) -> None:
    session, vault = _session(tmp_path)
    assert session.note_rows() == []

    note = Note.create(vault, "正文", title="标题")
    rows = session.note_rows()
    assert [row.oid for row in rows] == [str(note.oid)]
    assert rows[0].title == "标题"
    assert rows[0].preview == "正文"

    session.close()
    vault.close()


def test_update_invalidates_projection(tmp_path: Path) -> None:
    session, vault = _session(tmp_path)
    note = Note.create(vault, "一", title="旧")
    session.note_rows()

    note.update(title="新")
    assert session.note_rows()[0].title == "新"

    session.close()
    vault.close()


def test_delete_invalidates_projection(tmp_path: Path) -> None:
    session, vault = _session(tmp_path)
    note = Note.create(vault, "一")
    assert len(session.note_rows()) == 1

    vault.delete(note.oid)
    assert session.note_rows() == []

    session.close()
    vault.close()


def test_changed_signal_and_take_changed(tmp_path: Path) -> None:
    session, vault = _session(tmp_path)
    seen: list[str] = []
    session.changed.connect(seen.append)

    note = Note.create(vault, "一")
    assert str(note.oid) in seen
    assert session.take_changed() == [str(note.oid)]
    assert session.take_changed() == []

    session.close()
    vault.close()


def test_close_stops_listening(tmp_path: Path) -> None:
    session, vault = _session(tmp_path)
    session.close()
    Note.create(vault, "一")
    assert session.take_changed() == []
    vault.close()
