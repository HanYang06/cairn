# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""目录（catalog）：块身份到物理内容的映射。

目录是桶的**唯一真源**——位置只记录在这里，不做"可重建的派生索引"。
载体文件只追加、不平铺自描述；没有目录就无法定位内容，这是明确的取舍。

两张表：
    contents  物理内容，按 ``checksum`` 去重（同内容只存一次）
    blocks    逻辑块，稳定 ``id`` 指向一份 ``checksum``
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

CATALOG_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS packs(
  id INTEGER PRIMARY KEY,
  blocks INTEGER NOT NULL DEFAULT 0,
  bytes INTEGER NOT NULL DEFAULT 0,
  sealed INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS contents(
  checksum TEXT PRIMARY KEY,
  pack_id INTEGER NOT NULL,
  offset INTEGER NOT NULL,
  length INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS blocks(
  id TEXT PRIMARY KEY,
  checksum TEXT NOT NULL,
  type TEXT NOT NULL,
  size INTEGER NOT NULL DEFAULT 0,
  author TEXT NOT NULL DEFAULT '',
  config BLOB,
  meta BLOB,
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_blocks_checksum ON blocks(checksum);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


@dataclass(frozen=True, slots=True)
class BlockLocation:
    """内容在载体里的物理坐标。"""

    pack_id: int
    offset: int
    length: int


class Catalog:
    """``catalog.db`` 的读写封装。"""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('catalog_version', ?)",
            (str(CATALOG_VERSION),),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def commit(self) -> None:
        self.conn.commit()

    # ---- 载体 ----
    def open_pack(self, created: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO packs(blocks, bytes, sealed, created) VALUES(0, 0, 0, ?)",
            (created,),
        )
        return int(cursor.lastrowid or 0)

    def active_pack(self) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM packs WHERE sealed = 0 ORDER BY id DESC LIMIT 1"
        ).fetchone()

    def seal_pack(self, pack_id: int) -> None:
        self.conn.execute("UPDATE packs SET sealed = 1 WHERE id = ?", (pack_id,))

    def grow_pack(self, pack_id: int, nbytes: int) -> None:
        self.conn.execute(
            "UPDATE packs SET bytes = bytes + ?, blocks = blocks + 1 WHERE id = ?",
            (nbytes, pack_id),
        )

    def count_packs(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM packs").fetchone()
        return int(row["n"])

    # ---- 物理内容（按 checksum 去重）----
    def find_content(self, checksum: str) -> BlockLocation | None:
        row = self.conn.execute(
            "SELECT pack_id, offset, length FROM contents WHERE checksum = ?",
            (checksum,),
        ).fetchone()
        if row is None:
            return None
        return BlockLocation(
            pack_id=int(row["pack_id"]),
            offset=int(row["offset"]),
            length=int(row["length"]),
        )

    def add_content(self, checksum: str, location: BlockLocation) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO contents(checksum, pack_id, offset, length) "
            "VALUES(?, ?, ?, ?)",
            (checksum, location.pack_id, location.offset, location.length),
        )

    def count_contents(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM contents").fetchone()
        return int(row["n"])

    # ---- 逻辑块 ----
    def save_block(
        self,
        block_id: str,
        *,
        checksum: str,
        type: str,
        size: int,
        author: str,
        config: bytes,
        meta: bytes,
        created: int,
        updated: int,
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO blocks"
            "(id, checksum, type, size, author, config, meta, created, updated)"
            " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (block_id, checksum, type, size, author, config, meta, created, updated),
        )

    def block_row(self, block_id: str) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM blocks WHERE id = ?", (block_id,)).fetchone()

    def block_checksum(self, block_id: str) -> str | None:
        row = self.conn.execute(
            "SELECT checksum FROM blocks WHERE id = ?", (block_id,)
        ).fetchone()
        return None if row is None else str(row["checksum"])

    def has_block(self, block_id: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM blocks WHERE id = ?", (block_id,)).fetchone()
        return row is not None

    def remove_block(self, block_id: str) -> None:
        self.conn.execute("DELETE FROM blocks WHERE id = ?", (block_id,))

    def count_blocks(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM blocks").fetchone()
        return int(row["n"])

    def iter_block_ids(self) -> list[str]:
        rows = self.conn.execute("SELECT id FROM blocks ORDER BY id").fetchall()
        return [str(row["id"]) for row in rows]

    # ---- 通用表（供领域自描述的业务表用）----
    def table_exists(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        return row is not None

    def create_table(self, name: str, columns: dict[str, str]) -> None:
        parts = []
        for column, spec in columns.items():
            parts.append(f'"{column}" {spec}'.strip())
        self.conn.execute(f'CREATE TABLE IF NOT EXISTS "{name}" ({", ".join(parts)})')

    # ---- 元信息 ----
    def set_meta(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)",
            (key, value),
        )

    def get_meta(self, key: str) -> str | None:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return None if row is None else str(row["value"])


__all__ = ["CATALOG_VERSION", "BlockLocation", "Catalog"]
