# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import Vault
from feature import GroupData, Note, Relation
from feature.group import GroupError, all_gids, list_groups, roots

if TYPE_CHECKING:
    from pathlib import Path


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_create_assigns_gid_separate_from_oid(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    group = GroupData.create(vault, "工作", key="s3cret", owner="韩", member=["石"])

    assert group.gid
    assert group.gid != str(group.oid)
    assert group.title == "工作"
    assert group.lock is False
    assert group.key == "s3cret"
    assert group.owner == "韩"
    assert group.member == ["石"]
    assert [item.gid for item in list_groups(vault)] == [group.gid]


def test_add_note_stores_oid_and_relation(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    group = GroupData.create(vault, "收集")
    note = Note(vault).create("一条笔记")

    group.add(note)

    assert group.group == [str(note.oid)]
    links = list(Relation.backlinks(vault, note.oid, relation="contains"))
    assert [edge.source for edge in links] == [group.oid]


def test_nested_groups_store_gid_and_roots(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    parent = GroupData.create(vault, "父")
    child = GroupData.create(vault, "子", parent=parent)

    assert parent.group == [child.gid]
    assert child.gid in all_gids(vault)
    assert [group.gid for group in parent.subgroups()] == [child.gid]
    assert [group.gid for group in roots(vault)] == [parent.gid]


def test_lock_blocks_editing(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    group = GroupData.create(vault, "锁定")
    note = Note(vault).create("x")
    group.lock = True
    group.save()

    with pytest.raises(GroupError):
        group.add(note)
    with pytest.raises(GroupError):
        group.remove(note)


def test_move_reorders_children(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    group = GroupData.create(vault, "排序")
    notes = Note(vault)
    first = notes.create("一")
    second = notes.create("二")
    group.add(first)
    group.add(second)

    group.move([1, 0])

    assert group.group == [str(second.oid), str(first.oid)]


def test_roundtrip(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    group = GroupData.create(vault, "持久", key="k")
    note = Note(vault).create("内容")
    group.add(note)

    vault.close()
    reopened = Vault.load(tmp_path / "vault")
    loaded = GroupData.by_gid(reopened, group.gid)

    assert loaded is not None
    assert loaded.title == "持久"
    assert loaded.key == "k"
    assert loaded.group == [str(note.oid)]
