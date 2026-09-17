# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from PySide6.QtWidgets import QApplication

from cairn.ui.backend import Backend, NotesModel, TabsModel, open_vault

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def backend(qapp: QApplication, tmp_path: Path) -> Backend:
    assert QApplication.instance() is qapp
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
    backend.saveNow()  # 检查点：连续编辑的边界才记版本

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
    assert source in oids
    assert child in oids
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
        "vault",
        "author",
        "authors",
        "signature",
        "tags",
        "favorite",
        "archived",
        "visibility",
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


def test_line_edit_slots(backend: Backend) -> None:
    backend.createNote()
    first = backend.currentBlocks[0]["id"]

    backend.setLineText(first, "床前明月光")
    backend.flush()
    assert backend.currentText == "床前明月光"

    second = backend.splitLine(first, 4)
    backend.flush()
    texts = [block["text"] for block in backend.currentBlocks]
    assert texts == ["床前明月", "光"]

    merged = backend.mergeLine(second)
    backend.flush()
    assert merged == first
    assert backend.currentText == "床前明月光"

    inserted = backend.insertLineAfter(first, "疑是地上霜")
    backend.flush()
    assert inserted
    assert [block["text"] for block in backend.currentBlocks] == ["床前明月光", "疑是地上霜"]

    backend.removeLine(inserted)
    backend.flush()
    assert [block["text"] for block in backend.currentBlocks] == ["床前明月光"]


def test_run_tool_through_backend(backend: Backend) -> None:
    backend.captureNote("abcdef")
    lid = backend.currentBlocks[0]["id"]

    backend.runTool("bold", lid, 1, 3)
    backend.flush()
    styles = backend.currentBlocks[0]["styles"]
    assert styles[0][:2] == [1, 3]
    assert styles[0][2]["bold"] is True

    backend.runTool("align-center", lid, 0, 0)
    backend.flush()
    assert backend.currentBlocks[0]["para"] == {"align": "center"}

    assert len(backend.tools) > 0
    assert len(backend.toolLayout) == 2


def test_tool_state_and_groups(backend: Backend) -> None:
    backend.captureNote("abcdef")
    lid = backend.currentBlocks[0]["id"]

    state = backend.toolState(lid, 0, 0)
    assert state["bold"] is False
    assert state["favorite"] is False

    backend.runTool("bold", lid, 1, 3)
    backend.flush()
    assert backend.toolState(lid, 1, 3)["bold"] is True
    assert backend.toolState(lid, 0, 6)["bold"] is None

    backend.toggleFavorite(backend.currentOid)
    assert backend.toolState(lid, 0, 0)["favorite"] is True

    categories = {group["category"] for group in backend.toolGroups}
    assert {"add", "edit", "command", "query"} <= categories
    assert any(tool["id"] == "insert-code" for tool in backend.tools)


def test_insert_code_through_backend(backend: Backend) -> None:
    backend.captureNote("x")
    lid = backend.currentBlocks[0]["id"]

    new_id = backend.runTool("insert-code", lid, 0, 0)
    backend.flush()
    assert new_id
    assert new_id != lid

    blocks = backend.currentBlocks
    assert blocks[1]["id"] == new_id
    assert blocks[1]["para"] == {"block": "code"}


def test_set_paragraph_through_backend(backend: Backend) -> None:
    backend.captureNote("段")
    lid = backend.currentBlocks[0]["id"]

    backend.setParagraph(lid, {"align": "center", "heading": 2})
    backend.flush()
    assert backend.currentBlocks[0]["para"] == {"align": "center", "heading": 2}

    backend.clearParagraph(lid)
    backend.flush()
    assert backend.currentBlocks[0]["para"] == {}


def test_autosave_defers_version_until_checkpoint(backend: Backend) -> None:
    backend.captureNote("v1")
    assert len(backend.currentVersions) == 1

    lid = backend.currentBlocks[0]["id"]
    backend.setLineText(lid, "v2")
    backend.flush()  # 自动保存：只落盘
    assert len(backend.currentVersions) == 1
    assert backend.currentText == "v2"

    backend.saveNow()  # 检查点
    assert len(backend.currentVersions) == 2


def test_toggle_line_style_through_backend(backend: Backend) -> None:
    backend.captureNote("abcdef")
    lid = backend.currentBlocks[0]["id"]

    backend.toggleLineStyle(lid, 1, 3, "bold")
    backend.flush()

    styles = backend.currentBlocks[0]["styles"]
    assert styles == [
        [
            1,
            3,
            {
                "bold": True,
                "italic": False,
                "underline": False,
                "strike": False,
                "font": "",
                "color": "",
                "size": 0.0,
            },
        ]
    ]

    backend.toggleLineStyle(lid, 1, 3, "bold")
    backend.flush()
    assert backend.currentBlocks[0]["styles"] == []


def test_group_tree_membership(backend: Backend) -> None:
    oid = backend.captureNote("组内笔记")
    gid = backend.createGroup("工作")
    backend.addNoteToGroup(oid, gid)

    tree = backend.groupTree
    work = next(node for node in tree if node["gid"] == gid)
    assert work["title"] == "工作"
    assert [child["kind"] for child in work["children"]] == ["note"]
    assert work["children"][0]["oid"] == oid
    assert backend.groupChoices == [{"gid": gid, "title": "工作"}]


def test_group_nested_and_ungrouped(backend: Backend) -> None:
    oid = backend.captureNote("自由笔记")
    parent = backend.createGroup("父")
    child = backend.createGroup("子", parent)

    tree = backend.groupTree
    parent_node = next(node for node in tree if node["gid"] == parent)
    assert [node["gid"] for node in parent_node["children"]] == [child]

    ungrouped = next(node for node in tree if node["title"] == "未分组")
    assert [node["oid"] for node in ungrouped["children"]] == [oid]


def test_group_lock_blocks_membership(backend: Backend) -> None:
    oid = backend.captureNote("x")
    gid = backend.createGroup("锁")
    backend.toggleGroupLock(gid)
    backend.addNoteToGroup(oid, gid)

    node = next(node for node in backend.groupTree if node["gid"] == gid)
    assert node["lock"] is True
    assert node["children"] == []


def test_group_lock_blocks_rename(backend: Backend) -> None:
    gid = backend.createGroup("锁")
    backend.renameGroup(gid, "改名前")
    backend.toggleGroupLock(gid)
    backend.renameGroup(gid, "改名后")
    assert backend.groupChoices == [{"gid": gid, "title": "改名前"}]


def test_group_key_unlock_flow(backend: Backend) -> None:
    gid = backend.createGroup("密")
    backend.setGroupKey(gid, "pass123")

    node = next(node for node in backend.groupTree if node["gid"] == gid)
    assert node["has_key"] is True
    assert node["unlocked"] is False

    assert backend.unlockGroup(gid, "wrong") is False
    assert backend.unlockGroup(gid, "pass123") is True
    node = next(node for node in backend.groupTree if node["gid"] == gid)
    assert node["unlocked"] is True

    backend.setGroupKey(gid, "newpass")
    node = next(node for node in backend.groupTree if node["gid"] == gid)
    assert node["unlocked"] is False


def test_move_group_and_cycle_guard(backend: Backend) -> None:
    a = backend.createGroup("A")
    b = backend.createGroup("B")
    backend.moveGroup(b, a)

    node_a = next(node for node in backend.groupTree if node["gid"] == a)
    assert [node["gid"] for node in node_a["children"]] == [b]

    backend.moveGroup(a, b)  # 会成环，应拒绝
    roots = [node["gid"] for node in backend.groupTree if node["gid"] != ""]
    assert a in roots
    node_a = next(node for node in backend.groupTree if node["gid"] == a)
    node_b = next(child for child in node_a["children"] if child["gid"] == b)
    assert node_b["children"] == []


def test_reorder_in_group(backend: Backend) -> None:
    first = backend.captureNote("一")
    second = backend.captureNote("二")
    gid = backend.createGroup("组")
    backend.addNoteToGroup(first, gid)
    backend.addNoteToGroup(second, gid)

    backend.reorderInGroup(gid, second, -1)
    node = next(node for node in backend.groupTree if node["gid"] == gid)
    assert [child["oid"] for child in node["children"]] == [second, first]


def test_reorder_root_groups(backend: Backend) -> None:
    a = backend.createGroup("A")
    b = backend.createGroup("B")
    assert [node["gid"] for node in backend.groupTree] == [a, b]

    backend.reorderGroup(b, -1)
    assert [node["gid"] for node in backend.groupTree] == [b, a]


def test_filter_by_group(backend: Backend) -> None:
    inside = backend.captureNote("组内")
    backend.captureNote("组外")
    gid = backend.createGroup("组")
    backend.addNoteToGroup(inside, gid)

    backend.filterByGroup(gid)
    assert [node["gid"] for node in backend.groupTree] == [gid]

    backend.clearGroupFilter()
    assert backend.groupFilter == ""
    assert len(backend.groupTree) >= 1


def test_rename_and_delete_group(backend: Backend) -> None:
    gid = backend.createGroup("旧")
    backend.renameGroup(gid, "新")
    assert backend.groupChoices == [{"gid": gid, "title": "新"}]

    backend.deleteGroup(gid)
    assert backend.groupChoices == []


def test_search_notes_palette(backend: Backend) -> None:
    backend.captureNote("床前明月光")
    backend.captureNote("今天是个好天气")

    results = backend.searchNotes("明月")
    assert len(results) == 1
    assert results[0]["title"] == "床前明月光"
    assert results[0]["preview"] != ""

    assert backend.searchNotes("") == []
