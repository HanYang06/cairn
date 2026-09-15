# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记版本：**增量 diff 落 DB**，不做全量快照，避免块无限膨胀。

每条 diff 描述"从新内容回到上一版"要做的改动，形如：

    {"i": 2, "off": 3, "del": 4, "ins": "新文字"}    # 第 2 段第 3 字起，删 4 字，插入新文字
    {"i": 2, "del": 2, "ins": ["新段1", "新段2"]}     # 元素级：第 2 段起替换 2 段

当前版本永远在块里；历史按 diff 反向回放即可重建。
保留窗默认 30 天：**惰性压实**——用的时候（更新时）把过期 diff 丢掉。
"""

from __future__ import annotations

from typing import Any

from ...core.store import canonical, decode_canonical
from ...types import ObjectNotFoundError, now_ms

RETENTION_MS = 30 * 24 * 60 * 60 * 1000

_TABLE = "versions"
_COLUMNS = {
    "id": "TEXT PRIMARY KEY",
    "oid": "TEXT NOT NULL",
    "seq": "INTEGER NOT NULL",
    "at": "INTEGER NOT NULL",
    "diff": "BLOB",
}


def _table(vault: Any) -> Any:
    return vault.bucket.table(_TABLE, **_COLUMNS)


def _common_prefix(old: Any, new: Any) -> int:
    size = 0
    while size < len(old) and size < len(new) and old[size] == new[size]:
        size += 1
    return size


def _common_suffix(old: Any, new: Any, prefix: int) -> int:
    size = 0
    while (
        size < len(old) - prefix
        and size < len(new) - prefix
        and old[len(old) - 1 - size] == new[len(new) - 1 - size]
    ):
        size += 1
    return size


def diff_body(old: list[Any], new: list[Any]) -> dict[str, Any]:
    """算出把 ``old`` 变成 ``new`` 的最小单段改动。"""
    if old == new:
        return {}
    prefix = _common_prefix(old, new)
    suffix = _common_suffix(old, new, prefix)
    old_mid = old[prefix : len(old) - suffix]
    new_mid = new[prefix : len(new) - suffix]
    single = len(old_mid) == 1 and len(new_mid) == 1
    if single and isinstance(old_mid[0], str) and isinstance(new_mid[0], str):
        before, after = old_mid[0], new_mid[0]
        head = _common_prefix(before, after)
        tail = _common_suffix(before, after, head)
        return {
            "i": prefix,
            "off": head,
            "del": len(before) - head - tail,
            "ins": after[head : len(after) - tail],
        }
    return {"i": prefix, "del": len(old_mid), "ins": new_mid}


def apply_diff(body: list[Any], diff: dict[str, Any]) -> list[Any]:
    if not diff:
        return list(body)
    out = list(body)
    index = int(diff["i"])
    if "off" in diff:
        text = str(out[index])
        offset = int(diff["off"])
        remove = int(diff["del"])
        out[index] = text[:offset] + str(diff["ins"]) + text[offset + remove :]
    else:
        out[index : index + int(diff["del"])] = list(diff["ins"])
    return out


def record(vault: Any, oid: str, seq: int, frm: list[Any], to: list[Any]) -> None:
    """记录一条 diff：把 ``frm``（新版）变回 ``to``（上一版）。"""
    diff = diff_body(frm, to)
    if not diff:
        return
    _table(vault).insert(
        {
            "id": f"{oid}:{seq}",
            "oid": oid,
            "seq": seq,
            "at": now_ms(),
            "diff": canonical(diff),
        }
    )
    vault.bucket.commit()


def history(vault: Any, oid: str) -> list[dict[str, int]]:
    rows = _table(vault).select(oid=oid)
    return sorted(
        ({"seq": int(row["seq"]), "at": int(row["at"])} for row in rows),
        key=lambda item: item["seq"],
    )


def body_at(vault: Any, oid: str, seq: int, current_body: list[Any]) -> list[Any]:
    """从当前内容反向回放，重建第 ``seq`` 版。"""
    rows = {int(row["seq"]): row for row in _table(vault).select(oid=oid)}
    latest = max(rows) if rows else 1
    body = list(current_body)
    for step in range(latest, seq, -1):
        row = rows.get(step)
        if row is None:
            raise ObjectNotFoundError(f"版本缺失: {oid}@{step}")
        body = apply_diff(body, decode_canonical(bytes(row["diff"])))
    return body


def compact(vault: Any, oid: str, *, retention_ms: int | None = None) -> int:
    """惰性压实：丢掉超出保留窗的 diff。"""
    window = RETENTION_MS if retention_ms is None else retention_ms
    cutoff = now_ms() - window
    table = _table(vault)
    removed = 0
    for row in table.select(oid=oid):
        if int(row["at"]) < cutoff:
            table.delete(id=str(row["id"]))
            removed += 1
    if removed:
        vault.bucket.commit()
    return removed


__all__ = [
    "RETENTION_MS",
    "apply_diff",
    "body_at",
    "compact",
    "diff_body",
    "history",
    "record",
]
