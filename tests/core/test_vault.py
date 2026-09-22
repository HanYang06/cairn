# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from core import ObjectNotFoundError, Vault
from core.storage import Block

if TYPE_CHECKING:
    from pathlib import Path


def _create(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def _put(
    vault: Vault,
    body: bytes = b"",
    *,
    type: str = "blob",
    attrs: dict[str, Any] | None = None,
    id: str | None = None,
) -> Block:
    block = Block(id=id, body=body, attrs=dict(attrs or {}), type=type)
    vault.put_block(block)
    return block


def test_put_open_roundtrip(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    data = b"hello cairn " * 10_000
    block = _put(vault, data, type="note", attrs={"mime": "text/plain", "title": "hi"})
    with vault.open(block.id) as handle:
        assert handle.read() == data


def test_info_and_iter_filters(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    note = _put(vault, b"a", type="note", attrs={"title": "A", "tags": ["x"]})
    image = _put(vault, b"b", type="image", attrs={"mime": "image/png"})

    info = vault.info(note.id)
    assert info.type == "note"
    assert info.title == "A"
    assert info.tags == {"x": None}
    assert info.mime is None
    assert vault.info(image.id).mime == "image/png"

    assert [item.oid for item in vault.iter(type="note")] == [note.oid]
    assert {item.oid for item in vault.iter()} == {note.oid, image.oid}


def test_delete(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    block = _put(vault, b"x")
    vault.delete(block.id)
    with pytest.raises(ObjectNotFoundError):
        vault.open(block.id)


def test_persistence_across_reopen(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    block = _put(vault, b"persisted")
    vault.close()

    reopened = Vault.load(tmp_path / "vault")
    with reopened.open(block.id) as handle:
        assert handle.read() == b"persisted"


def test_identical_content_dedupes(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    data = b"same bytes " * 50_000
    _put(vault, data)
    before = vault.bucket.catalog.count_bodies()
    _put(vault, data)
    after = vault.bucket.catalog.count_bodies()
    assert before == after


def test_update_keeps_id_and_changes_content(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    first = _put(vault, b"v1", type="note", attrs={"title": "v1"})
    before = vault.info(first.id)

    _put(vault, b"v2", type="note", attrs={"title": "v2"}, id=first.id)

    after = vault.info(first.id)
    assert after.title == "v2"
    assert after.created == before.created
    assert after.updated >= before.updated
    with vault.open(first.id) as handle:
        assert handle.read() == b"v2"


def test_iter_filters_by_tags(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    both = _put(vault, b"a", type="note", attrs={"tags": ["x", "y"]})
    only_x = _put(vault, b"b", type="note", attrs={"tags": ["x"]})

    assert {info.oid for info in vault.iter(tags=["x"])} == {both.oid, only_x.oid}
    assert {info.oid for info in vault.iter(tags=["y"])} == {both.oid}
    assert {info.oid for info in vault.iter(tags=["z"])} == set()


def test_verify_reports_healthy(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    _put(vault, b"data " * 10_000)
    report = vault.verify()
    assert report.ok
    assert report.objects == 1


def test_unimplemented_maintenance_fails_loudly(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    with pytest.raises(NotImplementedError):
        vault.gc()
    with pytest.raises(NotImplementedError):
        vault.verify(deep=True)
