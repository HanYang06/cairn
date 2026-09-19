# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""桶：存储的载体，也是所有 I/O 的唯一入口。

桶**不是一个数据结构，而是一个类**：几乎没有字段，只有少量配置和方法。
它管三样东西——

    packs/       载体文件：一个文件装 N 个块，只追加；写满即封口
    catalog.db   目录：块 id / checksum → 物理位置的唯一真源
    业务表       领域自描述的表（``mount`` 建），供上层查询

用法是"对象编辑"：拿到对象、改字段、把整个对象交进来。

    note = bucket.new(Note)
    note.title = "x"
    bucket.put(note)
    same = bucket.get(Note, note.id)

数据库能力（事务 / 建表 / 查询）全部由桶封装，上层不 import sqlite：

    with bucket.transaction():
        bucket.put(note)
        notes = bucket.mount(Note)
        notes.upsert({"id": note.id, "title": note.title})

本地不加密；传输 / 服务端的加密不在这里。
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self

from core.types import (
    CairnError,
    CorruptObjectError,
    KindMismatchError,
    ObjectNotFoundError,
    now_ms,
)

from .block import INDEX_TYPE, PART_TYPE, Block, canonical, decode_canonical
from .catalog import BlockLocation, Catalog
from .table import Table

if TYPE_CHECKING:
    import builtins
    import sqlite3
    from collections.abc import Iterator

CATALOG_NAME = "catalog.db"
_CONFIG_KEY = "config"

# 去重只发生在领域对象层（note / project…）；内部分片块不做块级去重。
_NO_BLOCK_DEDUP = frozenset({PART_TYPE, INDEX_TYPE})


@dataclass(frozen=True, slots=True)
class BucketConfig:
    """桶的配置：只有开关和上限，没有业务语义。"""

    block_max_bytes: int = 1024 * 1024
    pack_max_blocks: int = 4096
    pack_max_bytes: int = 1024 * 1024 * 1024


class Bucket:
    """受管的文件系统：对象进、对象出，业务表随对象建。"""

    def __init__(self, root: Path, config: BucketConfig | None = None) -> None:
        self.root = Path(root)
        self.config = config or BucketConfig()
        self.packs_dir = self.root / "packs"
        self.catalog = Catalog(self.root / CATALOG_NAME)
        self._tx_depth = 0
        self._mounted: set[type[Block]] = set()

    # ---- 生命周期 ----
    @classmethod
    def create(cls, path: Path | str, config: BucketConfig | None = None) -> Bucket:
        root = Path(path)
        if (root / CATALOG_NAME).exists():
            raise CairnError(f"桶已存在: {root}")
        root.mkdir(parents=True, exist_ok=True)
        bucket = cls(root, config)
        bucket.packs_dir.mkdir(parents=True, exist_ok=True)
        bucket.catalog.set_meta(_CONFIG_KEY, json.dumps(asdict(bucket.config)))
        bucket.catalog.commit()
        return bucket

    @classmethod
    def open(cls, path: Path | str) -> Bucket:
        root = Path(path)
        if not (root / CATALOG_NAME).is_file():
            raise CairnError(f"不是有效的桶: {root}")
        bucket = cls(root)
        bucket.packs_dir.mkdir(parents=True, exist_ok=True)
        bucket.config = bucket._load_config()
        return bucket

    def close(self) -> None:
        self.catalog.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ---- 事务：把 SQLite 事务封在桶里 ----
    def _commit(self) -> None:
        if self._tx_depth == 0:
            self.catalog.commit()

    def commit(self) -> None:
        """显式提交当前挂起的变更（事务内为延后，交由 ``transaction`` 统一提交）。"""
        self._commit()

    @contextmanager
    def transaction(self) -> Iterator[Bucket]:
        """显式事务：块与业务表一起提交或一起回滚。"""
        self._tx_depth += 1
        try:
            yield self
        except BaseException:
            self._tx_depth -= 1
            if self._tx_depth == 0:
                self.catalog.conn.rollback()
            raise
        self._tx_depth -= 1
        if self._tx_depth == 0:
            self._commit()

    # ---- 对象编辑 API ----
    def new(self, cls: builtins.type[Block]) -> Block:
        """新建一个可编辑对象，id 已分配；此时尚未落盘。"""
        return cls()

    def put(self, block: Block) -> Block:
        """写入整个对象。返回同一个对象；body 按 ``body_hash`` 进内容池去重。"""
        block.validate()
        self.mount(type(block))
        checksum = block.body_hash()
        payload = block.encode_body()
        dedup = block.type not in _NO_BLOCK_DEDUP
        if not dedup or not self.body_exists(checksum):
            self._store_content(block, checksum, payload)
        self._save_block(block, checksum)
        self._commit()
        return block

    def get(self, cls: builtins.type[Block], block_id: str) -> Block:
        """按 id 取回可编辑对象，自动还原为 ``cls``。"""
        block = self._get(block_id)
        if not isinstance(block, cls):
            raise KindMismatchError(f"{block_id} 不是 {cls.__name__}（实际 {block.type}）")
        return block

    def delete(self, block_id: str) -> bool:
        """只摘逻辑块；物理内容留待压实回收。"""
        if not self.catalog.has_block(block_id):
            return False
        self.catalog.remove_block(block_id)
        self._commit()
        return True

    def has(self, block_id: str) -> bool:
        return self.catalog.has_block(block_id)

    # ---- body 去重池（O(1) 判重）----
    def body_exists(self, body_hash: str) -> bool:
        """该 body 是否已在池里（命中即可复用，不必再存）。"""
        return self.catalog.find_body(str(body_hash)) is not None

    @property
    def body_index(self) -> dict[str, list[str]]:
        """``{body_hash: [块 id, ...]}``——同 body 的块都在这；判重直接看 key。"""
        index: dict[str, list[str]] = {}
        for row in self.query("SELECT body_id, oid FROM block"):
            index.setdefault(str(row["body_id"]), []).append(str(row["oid"]))
        return index

    def iter_block_ids(self) -> Iterator[str]:
        yield from self.catalog.iter_block_ids()

    # ---- 数据库能力：领域自描述的表 ----
    def table(self, name: str, **columns: str) -> Table:
        """按需建表并返回句柄：``bucket.table("notes", id="TEXT PRIMARY KEY")``。"""
        if columns:
            self.catalog.create_table(name, columns)
            self._commit()
        return Table(self.catalog.conn, name)

    def mount(self, cls: builtins.type[Block]) -> builtins.type[Block]:
        """挂载领域类型：调用其 ``bind`` 完成关联建表等动作（幂等）。"""
        if cls not in self._mounted:
            cls.bind(self)
            self._mounted.add(cls)
        return cls

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> int:
        """逃生口：复杂 SQL 仍经桶执行，上层不 import sqlite。"""
        cursor = self.catalog.conn.execute(sql, list(params))
        self._commit()
        return cursor.rowcount

    def query(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> list[sqlite3.Row]:
        return list(self.catalog.conn.execute(sql, list(params)).fetchall())

    # ---- 大内容：分片 + 索引块 ----
    def put_content(
        self, data: bytes, *, kind: str = "asset", attrs: dict[str, Any] | None = None
    ) -> str:
        """写入一段内容：小则一块；大则分片，由索引块聚合成一个可引用的 id。"""
        if len(data) <= self.config.block_max_bytes:
            return self.put(Block(body=data, attrs=attrs, type=kind)).id
        step = self.config.block_max_bytes
        parts = [
            self.put(Block(body=data[start : start + step], type=PART_TYPE)).id
            for start in range(0, len(data), step)
        ]
        merged: dict[str, object] = dict(attrs or {})
        merged["kind"] = kind
        merged["size"] = len(data)
        return self.put(Block(body=parts, attrs=merged, type=INDEX_TYPE)).id

    def read_content(self, block_id: str) -> bytes:
        """还原 ``put_content`` 写入的原始字节（单块或分片皆可）。"""
        block = self._get(block_id)
        if block.type != INDEX_TYPE:
            return bytes(block.body)
        joined = bytearray()
        for part_id in block.body:
            joined += bytes(self._get(str(part_id)).body)
        return bytes(joined)

    # ---- 内部：块元数据 ----
    def _save_block(self, block: Block, checksum: str) -> None:
        now = now_ms()
        row = self.catalog.block_row(block.id)
        block.created = int(row["created"]) if row is not None else now
        block.updated = now
        block.size = block.content_size()
        block.checksum = checksum
        data = canonical({"attrs": block.attrs, "config": block.config, "author": block.author})
        self.catalog.save_block(
            block.id,
            body_id=checksum,
            type=self.catalog.type_code(block.type),
            size=block.size,
            data=data,
            created=block.created,
            updated=block.updated,
        )

    def _get(self, block_id: str) -> Block:
        row = self.catalog.block_row(block_id)
        if row is None:
            raise ObjectNotFoundError(block_id)
        checksum = str(row["body_id"])
        location = self.catalog.find_body(checksum)
        if location is None:
            raise CorruptObjectError(f"内容缺失: {checksum}")
        payload = self._read_pack(location)
        raw = decode_canonical(bytes(row["data"])) if row["data"] else {}
        params = raw if isinstance(raw, dict) else {}
        type_name = self.catalog.type_name(int(row["type"]))
        block = Block.decode(
            payload,
            id=block_id,
            attrs=dict(params.get("attrs") or {}),
            type=type_name,
        )
        if not block.verify():
            raise CorruptObjectError(f"块校验失败: {block_id}")
        block.size = int(row["size"])
        block.author = str(params.get("author") or "")
        block.config = dict(params.get("config") or {})
        block.created = int(row["created"])
        block.updated = int(row["updated"])
        return block

    def _store_content(self, block: Block, checksum: str, payload: bytes) -> BlockLocation:
        isolated = bool(block.config.get("isolated"))
        pack_id, offset = self._append(payload, isolated=isolated)
        location = BlockLocation(pack_id=pack_id, offset=offset, length=len(payload))
        self.catalog.add_body(checksum, location)
        return location

    def _read_pack(self, location: BlockLocation) -> bytes:
        path = self._pack_path(location.pack_id)
        try:
            with path.open("rb") as handle:
                handle.seek(location.offset)
                return handle.read(location.length)
        except FileNotFoundError as exc:
            raise CorruptObjectError(f"载体缺失: pack {location.pack_id}") from exc

    # ---- 内部：载体 ----
    def _load_config(self) -> BucketConfig:
        raw = self.catalog.get_meta(_CONFIG_KEY)
        if raw is None:
            return BucketConfig()
        try:
            return BucketConfig(**json.loads(raw))
        except (TypeError, ValueError):
            return BucketConfig()

    def _pack_path(self, pack_id: int) -> Path:
        return self.packs_dir / self.catalog.pack_name(pack_id)

    def _new_pack(self) -> int:
        pack_id = self.catalog.open_pack(now_ms())
        self._commit()
        return pack_id

    def _active_pack(self) -> int:
        row = self.catalog.active_pack()
        if row is not None:
            pack_id = int(row["id"])
            full = (
                int(row["blocks"]) >= self.config.pack_max_blocks
                or int(row["bytes"]) >= self.config.pack_max_bytes
            )
            if not full:
                return pack_id
            self.catalog.seal_pack(pack_id)
            self._commit()
        return self._new_pack()

    def _append(self, payload: bytes, *, isolated: bool = False) -> tuple[int, int]:
        pack_id = self._new_pack() if isolated else self._active_pack()
        path = self._pack_path(pack_id)
        with path.open("ab") as handle:
            offset = handle.tell()
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        self.catalog.grow_pack(pack_id, len(payload))
        if isolated:
            self.catalog.seal_pack(pack_id)
        return pack_id, offset


__all__ = ["CATALOG_NAME", "Bucket", "BucketConfig"]
