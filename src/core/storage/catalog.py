# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""目录（catalog）：块身份到物理内容的映射。

目录是桶的**唯一真源**——位置只记录在这里，不做"可重建的派生索引"。
载体文件只追加、不平铺自描述；没有目录就无法定位内容，这是明确的取舍。

表（单数、直白）：
    packs   载体文件：随机哈希命名，只追加
    body    body 池：``body_id``（哈希）→ 物理坐标，同内容只存一份（去重在此）
    block   逻辑块：稳定 ``oid`` 指向一份 ``body``
    meta    库级键值元信息
"""

from __future__ import annotations

import re
import secrets
import sqlite3
import string
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from core.types import CairnError, type_name

if TYPE_CHECKING:
    from collections.abc import Iterator

CATALOG_VERSION = 2

_NAME_ALPHABET = string.ascii_lowercase + string.digits
_NAME_LENGTH = 32
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS packs(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  blocks INTEGER NOT NULL DEFAULT 0,
  bytes INTEGER NOT NULL DEFAULT 0,
  sealed INTEGER NOT NULL DEFAULT 0,
  created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS body(
  body_id TEXT PRIMARY KEY,
  pack_id INTEGER NOT NULL,
  offset INTEGER NOT NULL,
  length INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS block_type(
  code INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);
INSERT OR IGNORE INTO block_type(code, name) VALUES
  (0, 'block'), (1, 'part'), (2, 'index');
CREATE TABLE IF NOT EXISTS block(
  oid TEXT PRIMARY KEY,
  body_id TEXT NOT NULL,
  type INTEGER NOT NULL,
  size INTEGER NOT NULL DEFAULT 0,
  data BLOB,
  created INTEGER NOT NULL,
  updated INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_block_body ON block(body_id);
CREATE INDEX IF NOT EXISTS idx_block_type ON block(type);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
"""


def _random_pack_name() -> str:
    """随机哈希命名载体文件（小写字母 + 数字，固定 32 位）。"""
    return "".join(secrets.choice(_NAME_ALPHABET) for _ in range(_NAME_LENGTH))


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
        self._check_version()
        self.conn.commit()

    def _check_version(self) -> None:
        """校验目录版本：新建时写入；已存在则只读，**不降级**（fail closed）。"""
        row = self.conn.execute("SELECT value FROM meta WHERE key = 'catalog_version'").fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO meta(key, value) VALUES('catalog_version', ?)",
                (str(CATALOG_VERSION),),
            )
            return
        try:
            stored = int(row["value"])
        except (TypeError, ValueError) as exc:
            raise CairnError(f"目录版本损坏: {row['value']!r}") from exc
        if stored > CATALOG_VERSION:
            raise CairnError(f"目录版本过新: {stored} > {CATALOG_VERSION}，请升级程序")

    def close(self) -> None:
        self.conn.close()

    def __del__(self) -> None:
        # 调用方忘记 close 时兜底释放 sqlite 句柄，避免 GC 期 ResourceWarning。
        with suppress(Exception):
            self.conn.close()

    def commit(self) -> None:
        self.conn.commit()

    # ---- 载体 ----
    def open_pack(self, created: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO packs(name, blocks, bytes, sealed, created) VALUES(?, 0, 0, 0, ?)",
            (_random_pack_name(), created),
        )
        return int(cursor.lastrowid or 0)

    def pack_name(self, pack_id: int) -> str:
        row = self.conn.execute("SELECT name FROM packs WHERE id = ?", (pack_id,)).fetchone()
        if row is None:
            raise CairnError(f"载体不存在: pack {pack_id}")
        return str(row["name"])

    def active_pack(self) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self.conn.execute(
            "SELECT * FROM packs WHERE sealed = 0 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row

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

    # ---- body 池（按 body_id 去重）----
    def find_body(self, body_id: str) -> BlockLocation | None:
        row = self.conn.execute(
            "SELECT pack_id, offset, length FROM body WHERE body_id = ?",
            (body_id,),
        ).fetchone()
        if row is None:
            return None
        return BlockLocation(
            pack_id=int(row["pack_id"]),
            offset=int(row["offset"]),
            length=int(row["length"]),
        )

    def add_body(self, body_id: str, location: BlockLocation) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO body(body_id, pack_id, offset, length) VALUES(?, ?, ?, ?)",
            (body_id, location.pack_id, location.offset, location.length),
        )

    def count_bodies(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM body").fetchone()
        return int(row["n"])

    # ---- 块类型码表（整数枚举；名字 ↔ code 稳定映射）----
    def type_code(self, name: str) -> int:
        key = type_name(name)
        row = self.conn.execute("SELECT code FROM block_type WHERE name = ?", (key,)).fetchone()
        if row is not None:
            return int(row["code"])
        assigned = self.conn.execute(
            "SELECT COALESCE(MAX(code), 15) + 1 AS code FROM block_type"
        ).fetchone()
        code = int(assigned["code"])
        self.conn.execute("INSERT INTO block_type(code, name) VALUES(?, ?)", (code, key))
        return code

    def find_type_code(self, name: str) -> int | None:
        """查类型码；**不存在返回 None**（不登记、不污染码表）。"""
        key = type_name(name)
        row = self.conn.execute("SELECT code FROM block_type WHERE name = ?", (key,)).fetchone()
        return None if row is None else int(row["code"])

    def type_name(self, code: int) -> str:
        row = self.conn.execute("SELECT name FROM block_type WHERE code = ?", (code,)).fetchone()
        if row is None:
            raise CairnError(f"未知块类型码: {code}")
        return str(row["name"])

    # ---- 逻辑块 ----
    def save_block(  # noqa: PLR0913 — 块行字段直接对应表列
        self,
        block_id: str,
        *,
        body_id: str,
        type: int,
        size: int,
        data: bytes,
        created: int,
        updated: int,
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO block(oid, body_id, type, size, data, created, updated)"
            " VALUES(?, ?, ?, ?, ?, ?, ?)",
            (block_id, body_id, int(type), size, data, created, updated),
        )

    def block_row(self, block_id: str) -> sqlite3.Row | None:
        row: sqlite3.Row | None = self.conn.execute(
            "SELECT * FROM block WHERE oid = ?", (block_id,)
        ).fetchone()
        return row

    def block_body_id(self, block_id: str) -> str | None:
        row = self.conn.execute("SELECT body_id FROM block WHERE oid = ?", (block_id,)).fetchone()
        return None if row is None else str(row["body_id"])

    def has_block(self, block_id: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM block WHERE oid = ?", (block_id,)).fetchone()
        return row is not None

    def remove_block(self, block_id: str) -> None:
        self.conn.execute("DELETE FROM block WHERE oid = ?", (block_id,))

    def count_blocks(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) AS n FROM block").fetchone()
        return int(row["n"])

    def iter_block_ids(self) -> Iterator[str]:
        cursor = self.conn.execute("SELECT oid FROM block ORDER BY oid")
        for row in cursor:
            yield str(row["oid"])

    # ---- 通用表（供领域自描述的业务表用）----
    def table_exists(self, name: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (name,)
        ).fetchone()
        return row is not None

    def create_table(self, name: str, columns: dict[str, str]) -> None:
        if not _IDENT_RE.match(name) or not all(_IDENT_RE.match(column) for column in columns):
            raise CairnError(f"非法表名或列名: {name}")
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
