# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core import Core  # noqa: TC001 — 运行期用来做类型断言
from feature import GroupData, Note, Relation
from feature.shared.group import GroupError, all_gids, list_groups, roots

if TYPE_CHECKING:
    from pathlib import Path


def test_create_assigns_gid_separate_from_oid(core: Core) -> None:

    group = GroupData.create(core, "工作", key="s3cret", owner="韩", member=["石"])

    assert group.gid
    assert group.gid != str(group.oid)
    assert group.title == "工作"
    assert group.lock is False
    assert group.key == "s3cret"
    assert group.owner == "韩"
    assert group.member == ["石"]
    assert [item.gid for item in list_groups(core)] == [group.gid]


def test_add_note_stores_oid_and_relation(core: Core) -> None:

    group = GroupData.create(core, "收集")
    note = Note(core).create("一条笔记")

    group.add(note)

    assert group.group == [str(note.oid)]
    links = list(Relation.backlinks(core, note.oid, relation="contains"))
    assert [edge.source for edge in links] == [group.oid]


def test_remove_deletes_contains_relation(core: Core) -> None:

    group = GroupData.create(core, "收集")
    note = Note(core).create("一条笔记")
    group.add(note)

    group.remove(note)

    assert group.group == []
    assert list(Relation.backlinks(core, note.oid, relation="contains")) == []


def test_readd_after_remove_leaves_one_relation(core: Core) -> None:

    group = GroupData.create(core, "收集")
    note = Note(core).create("一条笔记")
    group.add(note)
    group.remove(note)
    group.add(note)

    links = list(Relation.backlinks(core, note.oid, relation="contains"))

    assert group.group == [str(note.oid)]
    assert len(links) == 1


def test_remove_child_group_clears_relation(core: Core) -> None:

    parent = GroupData.create(core, "父")
    child = GroupData.create(core, "子", parent=parent)

    parent.remove(child)

    # 列表存 gid、关系行存 oid——拆边必须按建边时用的那个值
    assert parent.group == []
    assert list(Relation.backlinks(core, child.oid, relation="contains")) == []


def test_nested_groups_store_gid_and_roots(core: Core) -> None:

    parent = GroupData.create(core, "父")
    child = GroupData.create(core, "子", parent=parent)

    assert parent.group == [child.gid]
    assert child.gid in all_gids(core)
    assert [group.gid for group in parent.subgroups()] == [child.gid]
    assert [group.gid for group in roots(core)] == [parent.gid]


def test_lock_blocks_editing(core: Core) -> None:

    group = GroupData.create(core, "锁定")
    note = Note(core).create("x")
    group.lock = True
    group.save()

    with pytest.raises(GroupError):
        group.add(note)
    with pytest.raises(GroupError):
        group.remove(note)


def test_move_reorders_children(core: Core) -> None:

    group = GroupData.create(core, "排序")
    notes = Note(core)
    first = notes.create("一")
    second = notes.create("二")
    group.add(first)
    group.add(second)

    group.move([1, 0])

    assert group.group == [str(second.oid), str(first.oid)]


def test_move_requires_permutation(core: Core) -> None:

    group = GroupData.create(core, "排序")
    notes = Note(core)
    group.add(notes.create("一"))
    group.add(notes.create("二"))

    with pytest.raises(GroupError):
        group.move([0])
    with pytest.raises(GroupError):
        group.move([0, 0])


def test_roundtrip(core: Core, tmp_path: Path) -> None:

    group = GroupData.create(core, "持久", key="k")
    note = Note(core).create("内容")
    group.add(note)

    core.close()
    reopened = core.open(tmp_path / "vault")
    loaded = GroupData.by_gid(reopened, group.gid)

    assert loaded is not None
    assert loaded.title == "持久"
    assert loaded.key == "k"
    assert loaded.group == [str(note.oid)]
