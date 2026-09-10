from __future__ import annotations

from pathlib import Path

from cairn.core.pool import Pool, atomic_write
from cairn.core.types import Cid, Oid


def _pool(tmp_path: Path) -> Pool:
    pool = Pool(tmp_path / "pool")
    pool.ensure()
    return pool


def test_ensure_creates_layout(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    assert pool.chunks_dir.is_dir()
    assert pool.objects_dir.is_dir()
    assert pool.manifests_dir.is_dir()
    assert pool.spaces_dir.is_dir()


def test_chunk_write_read_and_dedupe(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    cid = Cid.from_digest(bytes(32))
    assert not pool.has_chunk(cid)
    assert pool.write_chunk(cid, b"blob") is True
    assert pool.write_chunk(cid, b"blob") is False
    assert pool.read_chunk(cid) == b"blob"
    assert list(pool.iter_chunk_cids()) == [cid]
    pool.delete_chunk(cid)
    assert not pool.has_chunk(cid)


def test_object_overwrite_and_iter(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    oid = Oid.new()
    pool.write_object(oid, b"m1")
    assert pool.read_object(oid) == b"m1"
    pool.write_object(oid, b"m2")
    assert pool.read_object(oid) == b"m2"
    assert list(pool.iter_object_ids()) == [oid]
    pool.delete_object(oid)
    assert list(pool.iter_object_ids()) == []


def test_manifest_archive_dedupe(tmp_path: Path) -> None:
    pool = _pool(tmp_path)
    digest = "ab" + "0" * 62
    assert pool.write_manifest(digest, b"x") is True
    assert pool.write_manifest(digest, b"x") is False
    assert pool.read_manifest(digest) == b"x"


def test_atomic_write_creates_parents(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "file.bin"
    atomic_write(target, b"data")
    assert target.read_bytes() == b"data"
