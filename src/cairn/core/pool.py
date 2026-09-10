"""对象池的落盘布局与原子读写。

本模块只负责"字节进、字节出"和目录分片、原子替换，不含任何加密语义。
"""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

from .types import Cid, Oid


def atomic_write(path: Path, data: bytes) -> None:
    """写临时文件 → fsync → 原子替换，保证崩溃一致性。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)
        raise


def prune_empty_dirs(directory: Path) -> None:
    """删除分片目录下的空子目录。"""
    if not directory.exists():
        return
    for shard in directory.iterdir():
        if shard.is_dir() and not any(shard.iterdir()):
            shard.rmdir()


class Pool:
    """按分片布局组织的块与清单仓库。"""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.chunks_dir = self.root / "chunks"
        self.objects_dir = self.root / "objects"
        self.manifests_dir = self.root / "manifests"
        self.spaces_dir = self.root / "spaces"

    def ensure(self) -> None:
        for directory in (
            self.chunks_dir,
            self.objects_dir,
            self.manifests_dir,
            self.spaces_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def chunk_path(self, cid: str) -> Path:
        name = str(cid)
        return self.chunks_dir / name[:2] / name

    def has_chunk(self, cid: str) -> bool:
        return self.chunk_path(cid).is_file()

    def write_chunk(self, cid: str, blob: bytes) -> bool:
        path = self.chunk_path(cid)
        if path.is_file():
            return False
        atomic_write(path, blob)
        return True

    def read_chunk(self, cid: str) -> bytes:
        return self.chunk_path(cid).read_bytes()

    def delete_chunk(self, cid: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            self.chunk_path(cid).unlink()

    def iter_chunk_cids(self) -> Iterator[Cid]:
        yield from self._iter_sharded(self.chunks_dir, Cid)

    def object_path(self, oid: str) -> Path:
        name = str(oid)
        return self.objects_dir / name[:2] / name

    def write_object(self, oid: str, blob: bytes) -> None:
        atomic_write(self.object_path(oid), blob)

    def read_object(self, oid: str) -> bytes:
        return self.object_path(oid).read_bytes()

    def delete_object(self, oid: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            self.object_path(oid).unlink()

    def iter_object_ids(self) -> Iterator[Oid]:
        yield from self._iter_sharded(self.objects_dir, Oid)

    def manifest_path(self, digest: str) -> Path:
        name = str(digest)
        return self.manifests_dir / name[:2] / name

    def write_manifest(self, digest: str, blob: bytes) -> bool:
        path = self.manifest_path(digest)
        if path.is_file():
            return False
        atomic_write(path, blob)
        return True

    def read_manifest(self, digest: str) -> bytes:
        return self.manifest_path(digest).read_bytes()

    def delete_manifest(self, digest: str) -> None:
        with contextlib.suppress(FileNotFoundError):
            self.manifest_path(digest).unlink()

    def iter_manifest_digests(self) -> Iterator[str]:
        yield from self._iter_sharded(self.manifests_dir, str)

    @staticmethod
    def _iter_sharded(directory: Path, factory: type) -> Iterator:
        if not directory.exists():
            return
        for shard in directory.iterdir():
            if shard.is_dir():
                for entry in shard.iterdir():
                    if entry.is_file() and not entry.name.startswith(".tmp-"):
                        yield factory(entry.name)
