# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核的读写面：对象**进 / 出 / 找**都经内核（表一里的存储是它的挂件）。

旧文件测的是已解散的 `Vault`；这里按新结构测 `Core`（内容一样，入口换成内核）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from core import Core, ObjectNotFoundError
from core.storage import Block

if TYPE_CHECKING:
    from pathlib import Path


def _put(
    core: Core,
    body: bytes = b"",
    *,
    type: str = "blob",
    attrs: dict[str, Any] | None = None,
    id: str | None = None,
) -> Block:
    block = Block(id=id, body=body, attrs=dict(attrs or {}), type=type)
    core.put(block)
    return block


def test_put_then_read_roundtrip(core: Core) -> None:
    data = b"hello cairn " * 10_000
    block = _put(core, data, type="note", attrs={"mime": "text/plain", "title": "hi"})

    assert core.read(block.id) == data


def test_info_and_iter_filters(core: Core) -> None:
    note = _put(core, b"a", type="note", attrs={"title": "A", "tags": ["x"]})
    image = _put(core, b"b", type="image", attrs={"mime": "image/png"})

    info = core.info(note.id)
    assert info.type == "note"
    assert info.title == "A"
    assert info.tags == {"x": None}
    assert info.mime is None
    assert core.info(image.id).mime == "image/png"

    assert [item.oid for item in core.iter(type="note")] == [note.oid]
    assert {item.oid for item in core.iter()} == {note.oid, image.oid}


def test_drop(core: Core) -> None:
    block = _put(core, b"x")
    core.drop(block.id)

    with pytest.raises(ObjectNotFoundError):
        core.read(block.id)


def test_persistence_across_reopen(core: Core, tmp_path: Path) -> None:
    block = _put(core, b"persisted")
    core.close()

    reopened = core.open(tmp_path / "vault")
    assert reopened.read(block.id) == b"persisted"


def test_identical_content_dedupes(core: Core) -> None:
    data = b"same bytes " * 50_000
    _put(core, data)
    before = core.storage.catalog.count_bodies()
    _put(core, data)
    after = core.storage.catalog.count_bodies()

    assert before == after  # 同 body 只存一份


def test_update_keeps_id_and_changes_content(core: Core) -> None:
    first = _put(core, b"v1", type="note", attrs={"title": "v1"})
    before = core.info(first.id)

    _put(core, b"v2", type="note", attrs={"title": "v2"}, id=first.id)

    after = core.info(first.id)
    assert after.title == "v2"
    assert after.created == before.created
    assert after.updated >= before.updated
    assert core.read(first.id) == b"v2"


def test_iter_filters_by_tags(core: Core) -> None:
    both = _put(core, b"a", type="note", attrs={"tags": ["x", "y"]})
    only_x = _put(core, b"b", type="note", attrs={"tags": ["x"]})

    assert {info.oid for info in core.iter(tags=["x"])} == {both.oid, only_x.oid}
    assert {info.oid for info in core.iter(tags=["y"])} == {both.oid}
    assert {info.oid for info in core.iter(tags=["z"])} == set()


def test_storage_ids_lists_every_object(core: Core) -> None:
    first = _put(core, b"a")
    second = _put(core, b"b")

    assert set(core.storage_ids()) == {first.id, second.id}
