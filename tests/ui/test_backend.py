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


def test_shares_are_additive(backend: Backend) -> None:
    backend.captureNote("笔记")
    assert backend.isPrivate
    assert backend.currentShares == []

    backend.addShare("homepage", "")
    backend.addShare("community", "Cairn 中文")
    backend.addShare("person", "韩")
    labels = [item["label"] for item in backend.currentShares]
    assert labels == ["个人主页", "社区 · Cairn 中文", "某人 · 韩"]
    assert not backend.isPrivate

    backend.removeShare("community", "Cairn 中文")
    assert [item["label"] for item in backend.currentShares] == ["个人主页", "某人 · 韩"]

    backend.toggleHomepage()
    assert [item["label"] for item in backend.currentShares] == ["某人 · 韩"]


def test_all_tags_and_filter(backend: Backend) -> None:
    backend.captureNote("甲")
    backend.addTag("设计")
    backend.captureNote("乙")
    backend.addTag("存储")

    assert backend.allTags == ["存储", "设计"]

    backend.openNote(backend.tabs.tab_keys()[0])
    backend.filterByTag("设计")
    assert backend.notes.rowCount() == 1
    backend.filterByTag("")
    assert backend.notes.rowCount() == 2


def test_profiles(backend: Backend) -> None:
    assert backend.currentAuthor == "本机"
    backend.createProfile("韩")
    assert backend.currentAuthor == "韩"
    backend.createProfile("石")
    assert backend.currentProfile == "石"
    backend.switchProfile("韩")
    assert backend.currentAuthor == "韩"
    assert backend.profiles == ["韩", "石"]


def test_views_relations_and_history(backend: Backend) -> None:
    oid = backend.captureNote("视图笔记")
    assert backend.currentView == "note"

    backend.openRelations()
    assert backend.currentView == "relations"
    assert backend.tabs.index_of("relations") >= 0

    backend.openHistory(oid)
    assert backend.currentView == "history"
    assert backend.currentVersions[0]["current"] is True

    backend.activateTab(oid)
    assert backend.currentView == "note"


def test_restore_version_through_backend(backend: Backend) -> None:
    backend.captureNote("第一版")
    backend.queueSave("第二版")
    backend.flush()

    versions = backend.currentVersions
    assert versions[0]["current"] is True
    assert [item["seq"] for item in versions] == [2, 1]
    assert backend.previewVersion(1) == "第一版"

    backend.restoreVersion(1)
    assert backend.currentText == "第一版"
    assert [item["seq"] for item in backend.currentVersions] == [3, 2, 1]


def test_graph_and_path(backend: Backend) -> None:
    source = backend.captureNote("源笔记")
    child = backend.deriveNote()

    graph = backend.currentGraph
    oids = {node["oid"] for node in graph["nodes"]}
    assert source in oids and child in oids
    assert any(edge["from"] == child and edge["to"] == source for edge in graph["edges"])

    path = backend.currentPath
    assert [item["oid"] for item in path] == [source, child]
    assert path[-1]["current"] is True


def _row_value(backend: Backend, oid: str, role: int) -> object:
    model = backend.notes
    for row in range(model.rowCount()):
        index = model.index(row, 0)
        if model.data(index, NotesModel.OidRole) == oid:
            return model.data(index, role)
    return None


def test_favorite_and_archive(backend: Backend) -> None:
    first = backend.captureNote("甲")
    backend.captureNote("乙")
    assert backend.notes.rowCount() == 2

    backend.toggleFavorite(first)
    assert backend.noteInfo(first)["favorite"] is True
    assert _row_value(backend, first, NotesModel.FavoriteRole) is True

    backend.toggleFavorite(first)
    assert backend.noteInfo(first)["favorite"] is False

    backend.toggleArchive(first)
    assert backend.noteInfo(first)["archived"] is True
    assert backend.showArchived is False
    assert backend.notes.rowCount() == 1

    backend.toggleShowArchived()
    assert backend.showArchived is True
    assert backend.notes.rowCount() == 2
    assert _row_value(backend, first, NotesModel.ArchivedRole) is True


def test_targeted_actions_do_not_switch_current(backend: Backend) -> None:
    source = backend.captureNote("源")
    current = backend.captureNote("当前")
    assert backend.currentOid == current

    backend.toggleHomepageOf(source)
    assert backend.noteInfo(source)["homepage"] is True
    assert backend.currentShares == []

    derived = backend.deriveFrom(source)
    assert derived != source
    assert backend.currentOid == derived
    assert [item["oid"] for item in backend.currentAncestors] == [source]


def test_current_properties_schema(backend: Backend) -> None:
    backend.captureNote("属性")
    backend.addTag("设计")

    props = {item["id"]: item for item in backend.currentProperties}
    assert set(props) == {
        "kind",
        "space",
        "author",
        "tags",
        "favorite",
        "archived",
        "created",
        "updated",
        "words",
        "size",
    }
    assert props["tags"]["value"] == ["设计"]
    assert props["tags"]["editable"] is True
    assert props["favorite"]["value"] is False

    backend.toggleFavorite(backend.currentOid)
    props = {item["id"]: item for item in backend.currentProperties}
    assert props["favorite"]["value"] is True


def test_trash_restore_and_purge(backend: Backend) -> None:
    oid = backend.captureNote("将删")
    assert backend.notes.rowCount() == 1

    backend.trashNote(oid)
    assert backend.notes.rowCount() == 0
    assert backend.trashedCount == 1

    backend.toggleShowTrash()
    assert backend.showTrash is True
    assert backend.notes.rowCount() == 1

    backend.restoreNote(oid)
    assert backend.trashedCount == 0

    backend.toggleShowTrash()
    assert backend.notes.rowCount() == 1

    backend.trashNote(oid)
    backend.emptyTrash()
    assert backend.trashedCount == 0
    assert backend.notes.rowCount() == 0


def test_share_targets_toggle(backend: Backend) -> None:
    backend.captureNote("分享")
    assert any(t["kind"] == "community" for t in backend.shareTargets)

    backend.toggleShareTo("community", "Cairn 中文")
    labels = [item["label"] for item in backend.currentShares]
    assert "社区 · Cairn 中文" in labels

    backend.toggleShareTo("community", "Cairn 中文")
    assert backend.currentShares == []


def test_tag_pairs_edit(backend: Backend) -> None:
    backend.captureNote("标签KV")
    backend.addTag("作者:韩")
    assert backend.tagPairs == [{"key": "作者", "value": "韩", "raw": "作者:韩"}]

    backend.replaceTag("作者:韩", "作者", "石")
    assert list(backend.currentTags) == ["作者"]
    assert backend.tagPairs[0]["value"] == "石"

    backend.replaceTag("作者:石", "", "")
    assert list(backend.currentTags) == []

    backend.addTag("项目:Cairn")
    backend.replaceTag("项目:Cairn", "项目", "")
    assert "项目" in backend.currentTags


def test_batch_tag_and_trash(backend: Backend) -> None:
    first = backend.captureNote("甲")
    second = backend.captureNote("乙")
    third = backend.captureNote("丙")

    backend.addTagToMany([first, second], "批")
    assert "批" in backend._vault.info(first).tags
    assert "批" in backend._vault.info(second).tags
    assert "批" not in backend._vault.info(third).tags

    backend.trashMany([first, second])
    assert backend.trashedCount == 2
    assert backend.notes.rowCount() == 1


def test_current_blocks_view(backend: Backend) -> None:
    backend.captureNote("第一行\n第二行")
    blocks = backend.currentBlocks
    assert [block["kind"] for block in blocks] == ["text", "text"]
    assert [block["text"] for block in blocks] == ["第一行", "第二行"]
    assert all(block["styles"] == [] for block in blocks)

    backend.queueSave("改\n后")
    backend.flush()
    assert [block["text"] for block in backend.currentBlocks] == ["改", "后"]
