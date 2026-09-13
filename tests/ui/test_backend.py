# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from cairn.ui.backend import Backend, NotesModel, TabsModel, open_vault


@pytest.fixture(scope="session")
def qt_app() -> Iterator[QCoreApplication]:
    app = QCoreApplication.instance() or QCoreApplication([])
    yield app


@pytest.fixture
def backend(qt_app: QCoreApplication, tmp_path: Path) -> Backend:
    assert QCoreApplication.instance() is qt_app
    return Backend(open_vault(tmp_path / "vault", "test-pass"))


def _titles(backend: Backend) -> list[str]:
    model = backend.notes
    return [
        str(model.data(model.index(row, 0), NotesModel.TitleRole))
        for row in range(model.rowCount())
    ]


def test_create_and_list(backend: Backend) -> None:
    assert backend.notes.rowCount() == 0
    oid = backend.createNote()
    assert backend.currentOid == oid
    assert backend.notes.rowCount() == 1
    assert _titles(backend) == ["新笔记"]


def test_capture_note_title_from_first_line(backend: Backend) -> None:
    oid = backend.captureNote("灵感：把收和编分开\n细节待定")
    assert oid != ""
    assert backend.currentTitle == "灵感：把收和编分开"
    assert "细节待定" in backend.currentText


def test_save_text_and_preview(backend: Backend) -> None:
    oid = backend.createNote()
    backend.queueSave("第一版")
    backend.flush()
    assert backend.currentText == "第一版"

    backend.queueSave("第二版")
    backend.flush()
    assert backend.currentText == "第二版"
    assert backend._vault.info(oid).title == "新笔记"

    model = backend.notes
    assert model.data(model.index(0, 0), NotesModel.PreviewRole) == "第二版"


def test_flush_on_switch(backend: Backend) -> None:
    first = backend.captureNote("笔记A")
    second = backend.captureNote("笔记B")

    backend.openNote(first)
    backend.queueSave("A 改过了")
    backend.openNote(second)
    backend.openNote(first)
    assert backend.currentText == "A 改过了"


def test_delete_current(backend: Backend) -> None:
    oid = backend.createNote()
    assert backend.currentOid == oid
    backend.deleteNote(oid)
    assert backend.currentOid == ""
    assert backend.notes.rowCount() == 0


def test_tabs_open_and_close(backend: Backend) -> None:
    a = backend.captureNote("笔记A")
    b = backend.captureNote("笔记B")
    assert backend.tabs.rowCount() == 2
    assert backend.currentOid == b

    backend.openNote(a)
    assert backend.currentOid == a

    backend.closeTab(a)
    assert backend.tabs.rowCount() == 1
    assert backend.currentOid == b

    backend.closeTab(b)
    assert backend.tabs.rowCount() == 0
    assert backend.currentOid == ""


def test_tags_add_remove(backend: Backend) -> None:
    backend.captureNote("带标签的笔记")
    backend.addTag("存储")
    backend.addTag("设计")
    backend.addTag("存储")
    assert list(backend.currentTags) == ["存储", "设计"]

    backend.removeTag("存储")
    assert list(backend.currentTags) == ["设计"]


def test_rename_updates_tab(backend: Backend) -> None:
    backend.captureNote("原名")
    backend.renameNote("改过的名字")
    index = backend.tabs.index(0, 0)
    assert backend.tabs.data(index, TabsModel.TitleRole) == "改过的名字"


def test_filter_notes_by_text(backend: Backend) -> None:
    backend.captureNote("苹果 笔记")
    backend.captureNote("香蕉 记录")
    assert backend.notes.rowCount() == 2

    backend.filterNotes("香蕉")
    assert backend.notes.rowCount() == 1

    backend.filterNotes("")
    assert backend.notes.rowCount() == 2


def test_derive_creates_lineage(backend: Backend) -> None:
    source = backend.captureNote("原始笔记")
    child = backend.deriveNote()

    assert child != source
    assert backend.currentOid == child
    assert [item["oid"] for item in backend.currentAncestors] == [source]

    backend.openNote(source)
    assert [item["oid"] for item in backend.currentDescendants] == [child]


def test_visibility_override_survives_edit(backend: Backend) -> None:
    backend.captureNote("笔记")
    assert backend.currentVisibility == "私密"

    backend.setVisibility("public")
    assert backend.currentVisibility == "公开"

    backend.queueSave("改过内容")
    backend.flush()
    assert backend.currentVisibility == "公开"
