# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cairn.core import ObjectNotFoundError, Vault

if TYPE_CHECKING:
    from pathlib import Path


def _create(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_put_open_roundtrip(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    data = b"hello cairn " * 10_000
    oid = vault.put(data, type="note", mime="text/plain", meta={"title": "hi"})
    with vault.open(oid) as handle:
        assert handle.read() == data


def test_info_and_iter_filters(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    note = vault.put(b"a", type="note", meta={"title": "A", "tags": ["x"]})
    image = vault.put(b"b", type="image", mime="image/png")

    info = vault.info(note)
    assert info.type == "note"
    assert info.title == "A"
    assert info.tags == {"x": None}
    assert info.mime is None

    assert vault.info(image).mime == "image/png"

    assert [item.oid for item in vault.iter(type="note")] == [note]
    assert {item.oid for item in vault.iter()} == {note, image}


def test_delete(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"x")
    vault.delete(oid)
    with pytest.raises(ObjectNotFoundError):
        vault.open(oid)


def test_persistence_across_reopen(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"persisted")
    vault.close()

    reopened = Vault.load(tmp_path / "vault")
    with reopened.open(oid) as handle:
        assert handle.read() == b"persisted"


def test_identical_content_dedupes(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    data = b"same bytes " * 50_000
    vault.put(data)
    before = vault.bucket.catalog.count_contents()
    vault.put(data)
    after = vault.bucket.catalog.count_contents()
    assert before == after


def test_put_from_path_and_file_object(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    source = tmp_path / "big.bin"
    data = b"pathy bytes " * 100_000
    source.write_bytes(data)

    from_path = vault.put(source)
    with vault.open(from_path) as handle:
        assert handle.read() == data

    with source.open("rb") as handle:
        from_file = vault.put(handle)
    with vault.open(from_file) as handle:
        assert handle.read() == data


def test_update_keeps_id_and_changes_content(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"v1", type="note", meta={"title": "v1"})
    before = vault.info(oid)

    same = vault.put(b"v2", oid=oid, type="note", meta={"title": "v2"})
    assert same == oid

    after = vault.info(oid)
    assert after.title == "v2"
    assert after.created == before.created
    assert after.updated >= before.updated
    with vault.open(oid) as handle:
        assert handle.read() == b"v2"


def test_put_meta_does_not_touch_body(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"body", type="note", meta={"title": "t1"})
    vault.put_meta(oid, meta={"title": "t2"})
    assert vault.info(oid).title == "t2"
    with vault.open(oid) as handle:
        assert handle.read() == b"body"


def test_iter_filters_by_tags(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    both = vault.put(b"a", type="note", meta={"tags": ["x", "y"]})
    only_x = vault.put(b"b", type="note", meta={"tags": ["x"]})

    assert {info.oid for info in vault.iter(tags=["x"])} == {both, only_x}
    assert {info.oid for info in vault.iter(tags=["y"])} == {both}
    assert {info.oid for info in vault.iter(tags=["z"])} == set()


def test_verify_reports_healthy(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    vault.put(b"data " * 10_000)
    report = vault.verify()
    assert report.ok
    assert report.objects == 1


def test_space_default(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    assert vault.space().name == "default"
    oid = vault.put(b"x")
    assert vault.info(oid).space_id == vault.space().space_id
