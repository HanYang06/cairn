# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""分组树投影 + 通用 TreeModel 测试。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

from cairn.core import Vault
from cairn.domains import Group, Note
from cairn.ui.models import TreeModel
from cairn.ui.rows import GroupNode
from cairn.ui.session import Session

if TYPE_CHECKING:
    from pathlib import Path


def test_group_nodes_nest_notes(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    note = Note.create(vault, "正文", title="甲")
    work = Group.create(vault, "工作")
    work.add(note)

    session = Session(vault)
    nodes = session.group_nodes()
    work_node = next(node for node in nodes if node.title == "工作")
    assert work_node.kind == "group"
    assert [child.key for child in work_node.children] == [str(note.oid)]
    assert work_node.children[0].kind == "note"

    session.close()
    vault.close()


def test_group_nodes_put_orphans_under_ungrouped(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    Note.create(vault, "正文", title="自由")

    session = Session(vault)
    nodes = session.group_nodes()
    ungrouped = next(node for node in nodes if node.title == "未分组")
    assert [child.title for child in ungrouped.children] == ["自由"]

    session.close()
    vault.close()


def test_tree_model_exposes_children_and_roles() -> None:
    roots = [
        GroupNode("group", "g1", "G1", (GroupNode("note", "n1", "N1"),)),
        GroupNode("note", "n2", "N2"),
    ]
    model: TreeModel[GroupNode] = TreeModel(
        [
            ("title", lambda node: node.title),
            ("key", lambda node: node.key),
            ("kind", lambda node: node.kind),
        ],
        lambda node: node.children,
        display="title",
    )
    model.set_roots(roots)

    assert model.rowCount() == 2
    group_index = model.index(0, 0)
    assert model.data(group_index, int(Qt.ItemDataRole.DisplayRole)) == "G1"
    assert model.rowCount(group_index) == 1

    child_index = model.index(0, 0, group_index)
    child = model.value_at(child_index)
    assert child is not None
    assert child.key == "n1"
    assert model.parent(child_index) == group_index
    assert model.data(model.index(1, 0), int(Qt.ItemDataRole.DisplayRole)) == "N2"
