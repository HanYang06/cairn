# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""表：受桶管的业务表，供上层查询用。

上层不需要 import sqlite，也不需要手写连接与事务——拿到 ``Table`` 句柄后
用方法操作即可。表由领域对象自描述（``Block.table`` / ``Block.columns``），
经 ``Bucket.mount`` 建出来。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Mapping


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class Table:
    """一张业务表的读写封装。"""

    def __init__(self, conn: sqlite3.Connection, name: str) -> None:
        self.conn = conn
        self.name = name

    def insert(self, row: Mapping[str, Any]) -> None:
        columns = list(row)
        placeholders = ", ".join("?" for _ in columns)
        names = ", ".join(_quote(column) for column in columns)
        self.conn.execute(
            f"INSERT INTO {_quote(self.name)} ({names}) VALUES({placeholders})",
            [row[column] for column in columns],
        )

    def upsert(self, row: Mapping[str, Any], *, conflict: str = "id") -> None:
        columns = list(row)
        placeholders = ", ".join("?" for _ in columns)
        names = ", ".join(_quote(column) for column in columns)
        self.conn.execute(
            f"INSERT OR REPLACE INTO {_quote(self.name)} ({names}) VALUES({placeholders})",
            [row[column] for column in columns],
        )
        _ = conflict

    def select(self, **where: Any) -> list[sqlite3.Row]:
        clause = ""
        if where:
            clause = " WHERE " + " AND ".join(f"{_quote(key)} = ?" for key in where)
        cursor = self.conn.execute(
            f"SELECT * FROM {_quote(self.name)}{clause}",
            list(where.values()),
        )
        return list(cursor.fetchall())

    def all(self) -> list[sqlite3.Row]:
        return self.select()

    def update(self, values: Mapping[str, Any], **where: Any) -> int:
        assignments = ", ".join(f"{_quote(key)} = ?" for key in values)
        clause = " AND ".join(f"{_quote(key)} = ?" for key in where)
        cursor = self.conn.execute(
            f"UPDATE {_quote(self.name)} SET {assignments} WHERE {clause}",
            [*values.values(), *where.values()],
        )
        return cursor.rowcount

    def delete(self, **where: Any) -> int:
        clause = " AND ".join(f"{_quote(key)} = ?" for key in where)
        cursor = self.conn.execute(
            f"DELETE FROM {_quote(self.name)} WHERE {clause}",
            list(where.values()),
        )
        return cursor.rowcount

    def count(self) -> int:
        row = self.conn.execute(f"SELECT COUNT(*) AS n FROM {_quote(self.name)}").fetchone()
        return int(row["n"])


__all__ = ["Table"]
