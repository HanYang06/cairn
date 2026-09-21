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


def _predicates(where: Mapping[str, Any]) -> tuple[str, list[Any]]:
    """把等值过滤编成子句与参数；``None`` 用 ``IS NULL``（``= NULL`` 永不命中）。"""
    clauses: list[str] = []
    values: list[Any] = []
    for key, value in where.items():
        if value is None:
            clauses.append(f"{_quote(key)} IS NULL")
        else:
            clauses.append(f"{_quote(key)} = ?")
            values.append(value)
    return " AND ".join(clauses), values


class Table:
    """一张业务表的读写封装。"""

    def __init__(self, conn: sqlite3.Connection, name: str) -> None:
        self.conn = conn
        self.name = name

    def insert(self, row: Mapping[str, Any]) -> None:
        columns = list(row)
        if not columns:
            raise ValueError("insert 需要至少一列")
        placeholders = ", ".join("?" for _ in columns)
        names = ", ".join(_quote(column) for column in columns)
        self.conn.execute(
            f"INSERT INTO {_quote(self.name)} ({names}) VALUES({placeholders})",
            [row[column] for column in columns],
        )

    def upsert(self, row: Mapping[str, Any], *, conflict: str = "id") -> None:
        """按 ``conflict`` 列做真 upsert（``ON CONFLICT DO UPDATE``），保留未列出的列。

        ``conflict`` 不在行内时退回 ``INSERT OR REPLACE``（兼容按表自身主键去重的旧调用）。
        """
        columns = list(row)
        if not columns:
            raise ValueError("upsert 需要至少一列")
        placeholders = ", ".join("?" for _ in columns)
        names = ", ".join(_quote(column) for column in columns)
        values = [row[column] for column in columns]
        if conflict in columns:
            updates = ", ".join(
                f"{_quote(column)} = excluded.{_quote(column)}"
                for column in columns
                if column != conflict
            )
            action = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
            sql = (
                f"INSERT INTO {_quote(self.name)} ({names}) VALUES({placeholders}) "
                f"ON CONFLICT({_quote(conflict)}) {action}"
            )
        else:
            sql = f"INSERT OR REPLACE INTO {_quote(self.name)} ({names}) VALUES({placeholders})"
        self.conn.execute(sql, values)

    def select(self, **where: Any) -> list[sqlite3.Row]:
        if where:
            clause, values = _predicates(where)
            sql = f"SELECT * FROM {_quote(self.name)} WHERE {clause}"
        else:
            sql, values = f"SELECT * FROM {_quote(self.name)}", []
        return list(self.conn.execute(sql, values).fetchall())

    def all(self) -> list[sqlite3.Row]:
        return self.select()

    def update(self, values: Mapping[str, Any], **where: Any) -> int:
        if not values:
            raise ValueError("update 需要至少一列")
        if not where:
            raise ValueError("update 需要至少一个过滤条件")
        assignments = ", ".join(f"{_quote(key)} = ?" for key in values)
        clause, filter_values = _predicates(where)
        cursor = self.conn.execute(
            f"UPDATE {_quote(self.name)} SET {assignments} WHERE {clause}",
            [*values.values(), *filter_values],
        )
        return cursor.rowcount

    def delete(self, **where: Any) -> int:
        if not where:
            raise ValueError("delete 需要至少一个过滤条件")
        clause, values = _predicates(where)
        cursor = self.conn.execute(
            f"DELETE FROM {_quote(self.name)} WHERE {clause}",
            values,
        )
        return cursor.rowcount

    def count(self) -> int:
        row = self.conn.execute(f"SELECT COUNT(*) AS n FROM {_quote(self.name)}").fetchone()
        return int(row["n"])


__all__ = ["Table"]
