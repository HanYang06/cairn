from __future__ import annotations

from pathlib import Path

from cairn.core.storage.index import Index
from cairn.core.vault import Vault

PASSPHRASE = "correct horse battery staple"


def _create(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", PASSPHRASE)


def test_rebuild_index_counts_objects(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    note = vault.put(b"a", type="note", meta={"title": "A", "tags": ["x", "y"]})
    image = vault.put(b"b", type="image", mime="image/png")

    assert vault.rebuild_index() == 2

    index = Index(tmp_path / "vault" / ".cairn" / "index.sqlite")
    try:
        assert index.count() == 2
        assert index.count("spaces") == 1
        assert index.count("chunks") >= 1

        notes = index.list_objects(type="note")
        assert [row["oid"] for row in notes] == [str(note)]
        assert notes[0]["title"] == "A"

        images = index.list_objects(type="image")
        assert [row["oid"] for row in images] == [str(image)]
    finally:
        index.close()


def test_index_rebuild_is_idempotent(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    vault.put(b"a", type="note")
    vault.put(b"b", type="note")
    assert vault.rebuild_index() == 2
    assert vault.rebuild_index() == 2

    index = Index(tmp_path / "vault" / ".cairn" / "index.sqlite")
    try:
        assert index.count() == 2
    finally:
        index.close()


def test_index_reflects_deletion_after_rebuild(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    keep = vault.put(b"keep", type="note")
    drop = vault.put(b"drop", type="note")
    vault.delete(drop)
    assert vault.rebuild_index() == 1

    index = Index(tmp_path / "vault" / ".cairn" / "index.sqlite")
    try:
        assert [row["oid"] for row in index.list_objects()] == [str(keep)]
    finally:
        index.close()


def test_gc_removes_orphan_chunks(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"data " * 100_000)
    total = len(list(vault.pool.iter_chunk_cids()))
    assert total > 0

    vault.delete(oid)
    assert vault.gc() == total
    assert list(vault.pool.iter_chunk_cids()) == []


def test_gc_keeps_chunks_shared_by_survivors(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    data = b"shared bytes " * 50_000
    first = vault.put(data)
    second = vault.put(data)

    vault.delete(first)
    assert vault.gc() == 0
    with vault.open(second) as handle:
        assert handle.read() == data


def test_gc_keeps_live_chunks(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"live " * 50_000)
    assert vault.gc() == 0
    with vault.open(oid) as handle:
        assert handle.read() == b"live " * 50_000


def test_index_updates_incrementally(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    vault.rebuild_index()

    note = vault.put(b"a", type="note")
    vault.put(b"b", type="image")

    index = Index(tmp_path / "vault" / ".cairn" / "index.sqlite")
    try:
        assert index.count() == 2
        assert index.count("spaces") == 1
    finally:
        index.close()

    vault.delete(note)

    index = Index(tmp_path / "vault" / ".cairn" / "index.sqlite")
    try:
        assert index.count() == 1
        assert index.list_objects(type="note") == []
    finally:
        index.close()

