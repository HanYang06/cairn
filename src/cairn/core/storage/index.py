# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""SQLite 索引：由 manifest 派生，可全量重建。

索引是派生物，随时可丢；磁盘上的 manifest 才是真源。
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from ..types import now_ms

if TYPE_CHECKING:
    from ..types import Oid, Space
    from ..vault import Vault
    from .manifest import Manifest

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS spaces(
  space_id TEXT PRIMARY KEY,
  name TEXT,
  visibility TEXT,
  key_epoch INTEGER DEFAULT 1,
  created INTEGER
);
CREATE TABLE IF NOT EXISTS objects(
  oid TEXT PRIMARY KEY,
  space_id TEXT,
  type TEXT,
  mime TEXT,
  size INTEGER,
  created INTEGER,
  updated INTEGER,
  seq INTEGER,
  author TEXT,
  title TEXT,
  manifest_mtime INTEGER
);
CREATE INDEX IF NOT EXISTS idx_objects_space ON objects(space_id);
CREATE INDEX IF NOT EXISTS idx_objects_type ON objects(type);
CREATE TABLE IF NOT EXISTS obj_tags(
  oid TEXT,
  tag TEXT,
  PRIMARY KEY(oid, tag)
);
CREATE TABLE IF NOT EXISTS obj_chunks(
  oid TEXT,
  idx INTEGER,
  cid TEXT,
  size INTEGER,
  PRIMARY KEY(oid, idx)
);
CREATE TABLE IF NOT EXISTS chunks(
  cid TEXT PRIMARY KEY,
  size INTEGER,
  refcount INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS object_text(
  oid TEXT PRIMARY KEY,
  body TEXT
);
CREATE TABLE IF NOT EXISTS links(
  src_oid TEXT,
  dst_oid TEXT,
  kind TEXT
);
CREATE TABLE IF NOT EXISTS meta(
  key TEXT PRIMARY KEY,
  value TEXT
);
"""


class Index:
    """``.cairn/index.sqlite`` 的读写封装。"""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self._fts = False
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(_SCHEMA)
        try:
            self.conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS search_fts "
                "USING fts5(oid UNINDEXED, body)"
            )
            self._fts = True
        except sqlite3.OperationalError:
            self._fts = False
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('index_format_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def clear(self) -> None:
        for table in (
            "spaces",
            "objects",
            "obj_tags",
            "obj_chunks",
            "chunks",
            "object_text",
            "links",
        ):
            self.conn.execute(f"DELETE FROM {table}")
        if self._fts:
            self.conn.execute("DELETE FROM search_fts")

    def add_space(self, space: Space) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO spaces(space_id, name, visibility, key_epoch, created) "
            "VALUES(?, ?, ?, 1, ?)",
            (str(space.space_id), space.name, space.visibility.value, space.created),
        )

    def add(
        self,
        manifest: Manifest,
        *,
        mtime_ms: int | None = None,
        previous: Manifest | None = None,
        search_text: str | None = None,
    ) -> None:
        if previous is not None:
            self._decref(previous.oid)
        meta = manifest.meta or {}
        oid = str(manifest.oid)
        self.conn.execute(
            "INSERT OR REPLACE INTO objects("
            "oid, space_id, type, mime, size, created, updated, seq, author, title, manifest_mtime"
            ") VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                oid,
                str(manifest.space_id),
                manifest.type,
                manifest.mime,
                manifest.size,
                manifest.created,
                manifest.updated,
                manifest.seq,
                manifest.author.hex(),
                meta.get("title"),
                mtime_ms,
            ),
        )
        self.conn.execute("DELETE FROM obj_tags WHERE oid = ?", (oid,))
        for tag in meta.get("tags") or ():
            self.conn.execute(
                "INSERT OR IGNORE INTO obj_tags(oid, tag) VALUES(?, ?)", (oid, str(tag))
            )
        self.conn.execute("DELETE FROM obj_chunks WHERE oid = ?", (oid,))
        for position, ref in enumerate(manifest.chunks):
            self.conn.execute(
                "INSERT OR REPLACE INTO obj_chunks(oid, idx, cid, size) VALUES(?, ?, ?, ?)",
                (oid, position, str(ref.cid), ref.size),
            )
        self._write_text(oid, search_text)
        self._incref(manifest)

    def _write_text(self, oid: str, search_text: str | None) -> None:
        self.conn.execute("DELETE FROM object_text WHERE oid = ?", (oid,))
        if search_text:
            self.conn.execute(
                "INSERT OR REPLACE INTO object_text(oid, body) VALUES(?, ?)",
                (oid, search_text),
            )
        if self._fts:
            self.conn.execute("DELETE FROM search_fts WHERE oid = ?", (oid,))
            if search_text:
                self.conn.execute(
                    "INSERT INTO search_fts(oid, body) VALUES(?, ?)", (oid, search_text)
                )

    @property
    def has_fts(self) -> bool:
        return self._fts

    def search(self, query: str) -> list[str]:
        """按正文子串检索，返回命中的 oid。

        注意：FTS5 的 unicode61 分词器不切分中日韩文，``MATCH`` 对中文无效；
        因此这里统一走 ``LIKE`` 子串匹配（对 CJK 与任意子串都正确）。
        """
        query = query.strip()
        if not query:
            return []
        rows = self.conn.execute(
            "SELECT oid FROM object_text WHERE body LIKE ?", (f"%{query}%",)
        ).fetchall()
        return [str(row["oid"]) for row in rows]

    def remove(self, oid: Oid | str) -> None:
        target = str(oid)
        self._decref(target)
        for table in ("objects", "obj_tags", "obj_chunks", "object_text"):
            self.conn.execute(f"DELETE FROM {table} WHERE oid = ?", (target,))
        if self._fts:
            self.conn.execute("DELETE FROM search_fts WHERE oid = ?", (target,))

    def _incref(self, manifest: Manifest) -> None:
        for ref in manifest.chunks:
            cid = str(ref.cid)
            self.conn.execute(
                "INSERT OR IGNORE INTO chunks(cid, size, refcount) VALUES(?, ?, 0)",
                (cid, ref.size),
            )
            self.conn.execute(
                "UPDATE chunks SET refcount = refcount + 1 WHERE cid = ?", (cid,)
            )

    def _decref(self, oid: Oid | str) -> None:
        rows = self.conn.execute(
            "SELECT cid FROM obj_chunks WHERE oid = ?", (str(oid),)
        ).fetchall()
        for row in rows:
            self.conn.execute(
                "UPDATE chunks SET refcount = refcount - 1 WHERE cid = ?", (row["cid"],)
            )
            self.conn.execute(
                "DELETE FROM chunks WHERE cid = ? AND refcount <= 0", (row["cid"],)
            )

    def commit(self) -> None:
        self.conn.commit()

    def recount_chunks(self) -> None:
        self.conn.execute("DELETE FROM chunks")
        self.conn.execute(
            "INSERT INTO chunks(cid, size, refcount) "
            "SELECT cid, MAX(size), COUNT(*) FROM obj_chunks GROUP BY cid"
        )

    def rebuild(self, vault: Vault, *, text_of: Callable[[Manifest], str] | None = None) -> int:
        self.clear()
        for space in vault.spaces():
            self.add_space(space)
        count = 0
        for manifest in vault.iter_manifests():
            try:
                mtime = int(vault.pool.object_path(manifest.oid).stat().st_mtime * 1000)
            except OSError:
                mtime = None
            search_text = text_of(manifest) if text_of is not None else None
            self.add(manifest, mtime_ms=mtime, search_text=search_text)
            count += 1
        self.recount_chunks()
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key, value) VALUES('built_at', ?)",
            (str(now_ms()),),
        )
        self.conn.commit()
        return count

    def count(self, table: str = "objects") -> int:
        row = self.conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
        return int(row["n"])

    def list_objects(
        self,
        *,
        space_id: str | None = None,
        type: str | None = None,
    ) -> list[sqlite3.Row]:
        clauses: list[str] = []
        params: list[object] = []
        if space_id is not None:
            clauses.append("space_id = ?")
            params.append(space_id)
        if type is not None:
            clauses.append("type = ?")
            params.append(type)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor = self.conn.execute(f"SELECT * FROM objects{where} ORDER BY oid", params)
        return list(cursor.fetchall())
