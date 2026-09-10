from __future__ import annotations

from pathlib import Path

import pytest

from cairn.core import (
    ObjectNotFoundError,
    SpaceNotFoundError,
    Vault,
    VaultLockedError,
    Visibility,
)
from cairn.core.types import AuthError

PASSPHRASE = "correct horse battery staple"


def _create(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", PASSPHRASE)


def test_put_open_roundtrip_multi_chunk(tmp_path: Path) -> None:
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
    assert info.tags == ("x",)

    assert [item.oid for item in vault.iter(type="note")] == [note]
    assert {item.oid for item in vault.iter()} == {note, image}


def test_delete(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"x")
    vault.delete(oid)
    with pytest.raises(ObjectNotFoundError):
        vault.open(oid)


def test_locked_vault_rejects_operations(tmp_path: Path) -> None:
    _create(tmp_path)
    vault = Vault.load(tmp_path / "vault")
    assert vault.is_locked
    with pytest.raises(VaultLockedError):
        vault.put(b"x")


def test_wrong_passphrase(tmp_path: Path) -> None:
    _create(tmp_path)
    vault = Vault.load(tmp_path / "vault")
    with pytest.raises(AuthError):
        vault.unlock("wrong passphrase")


def test_persistence_across_reopen(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"persisted")
    vault.lock()

    reopened = Vault.load(tmp_path / "vault")
    reopened.unlock(PASSPHRASE)
    with reopened.open(oid) as handle:
        assert handle.read() == b"persisted"


def test_identical_content_shares_chunks(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    data = b"same bytes " * 50_000
    vault.put(data)
    before = len(list(vault.pool.iter_chunk_cids()))
    vault.put(data)
    after = len(list(vault.pool.iter_chunk_cids()))
    assert before == after


def test_create_space_isolates_objects(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    space = vault.create_space("photos")
    assert space.visibility is Visibility.PRIVATE

    oid = vault.put(b"pic", space="photos", type="image")
    assert vault.info(oid).space_id == space.space_id
    assert [item.oid for item in vault.iter(space="photos")] == [oid]

    with pytest.raises(SpaceNotFoundError):
        vault.put(b"x", space="missing")


def test_space_persists_after_reopen(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    space = vault.create_space("photos")
    oid = vault.put(b"pic", space="photos")
    vault.lock()

    reopened = Vault.load(tmp_path / "vault")
    reopened.unlock(PASSPHRASE)
    assert reopened.info(oid).space_id == space.space_id


def test_put_from_path_streams(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    source = tmp_path / "big.bin"
    data = b"pathy bytes " * 100_000
    source.write_bytes(data)

    oid = vault.put(source)
    with vault.open(oid) as handle:
        assert handle.read() == data


def test_put_from_file_object(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    source = tmp_path / "obj.bin"
    data = b"object bytes " * 100_000
    source.write_bytes(data)

    with source.open("rb") as handle:
        oid = vault.put(handle)
    with vault.open(oid) as handle:
        assert handle.read() == data


def test_update_creates_version_chain(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"v1", type="note", meta={"title": "v1"})
    before = vault.info(oid)

    same = vault.put(b"v2", oid=oid, type="note", meta={"title": "v2"})
    assert same == oid

    after = vault.info(oid)
    assert after.title == "v2"
    assert after.created == before.created
    assert after.updated >= before.updated

    _, manifest = vault._load_manifest(oid)
    assert manifest.seq == 2
    assert manifest.prev is not None


def test_history_chunks_survive_until_delete(tmp_path: Path) -> None:
    vault = _create(tmp_path)
    oid = vault.put(b"old content " * 100_000)
    first_gen = len(list(vault.pool.iter_chunk_cids()))

    vault.put(b"brand new " * 100_000, oid=oid)
    second_gen = len(list(vault.pool.iter_chunk_cids()))
    assert second_gen > first_gen

    assert vault.gc() == 0
    assert len(list(vault.pool.iter_chunk_cids())) == second_gen

    vault.delete(oid)
    assert vault.gc() == second_gen
    assert list(vault.pool.iter_chunk_cids()) == []

