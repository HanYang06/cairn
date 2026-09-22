# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""版本引擎：通用的**变更链**，供各领域复用（block 亲和）。

它只管链、顺序、回放、压实，**不认识任何领域语义**；域提供 ``Codec``：

    Codec.digest(state)            -> 内容签名（进版本 id）
    Codec.diff(new_state, old)     -> 反向补丁（新 → 旧），可序列化
    Codec.apply(state, patch)      -> 应用反向补丁得到旧状态

约定（见文档）：
- 版本 id = ``blake3(canonical({prev, at, sig}))``：哈希身份 + ``prev`` 单亲链，
  顺序从 head 沿 ``prev`` 走，不依赖时间。
- 当前版本永远在块里；历史只存反向补丁（残页），从 head 反向回放。
- 保留窗默认 30 天，更新时惰性压实（丢链尾）。
- **不设 head 表**：head / count 由 ``version`` 表直接推导（谁不被任何 ``prev`` 指向即 head）。
"""

from __future__ import annotations

from typing import Any, Protocol

from blake3 import blake3

from core.types import ObjectNotFoundError, now_ms

from .block import canonical, decode_canonical

RETENTION_MS = 30 * 24 * 60 * 60 * 1000

_TABLE = "version"
_COLUMNS = {
    "id": "TEXT PRIMARY KEY",
    "oid": "TEXT NOT NULL",
    "prev": "TEXT",
    "at": "INTEGER NOT NULL",
    "payload": "BLOB",
}


class Codec(Protocol):
    """域提供的状态编解码器。"""

    def digest(self, state: Any) -> str: ...

    def diff(self, new_state: Any, old_state: Any) -> bytes: ...

    def apply(self, state: Any, patch: Any) -> Any: ...


def version_id(prev: str | None, at: int, sig: str) -> str:
    """版本 id：承诺 ``prev`` 与内容签名，顺序因此可回溯。"""
    return blake3(canonical({"prev": prev or "", "at": int(at), "sig": str(sig)})).hexdigest()


class VersionStore:
    """某库里全部块的版本链。"""

    def __init__(self, bucket: Any) -> None:
        self._bucket = bucket
        self._table = bucket.table(_TABLE, **_COLUMNS)

    # ---- 写 ----
    def root(self, oid: Any, codec: Codec, state: Any, *, at: int | None = None) -> str | None:
        """记下链的起点（初始版本）；已存在 head 则跳过。"""
        if self.head(oid) is not None:
            return None
        moment = now_ms() if at is None else int(at)
        vid = version_id(None, moment, codec.digest(state))
        self._table.insert(
            {"id": vid, "oid": str(oid), "prev": None, "at": moment, "payload": canonical({})}
        )
        self._bucket.commit()
        return vid

    def commit(
        self,
        oid: Any,
        codec: Codec,
        old_state: Any,
        new_state: Any,
        *,
        at: int | None = None,
    ) -> str | None:
        """记录一次变更；无变化返回 ``None``。"""
        payload = codec.diff(new_state, old_state)
        if not payload:
            return None
        moment = now_ms() if at is None else int(at)
        prev = self.head(oid)
        vid = version_id(prev, moment, codec.digest(new_state))
        self._table.insert(
            {"id": vid, "oid": str(oid), "prev": prev, "at": moment, "payload": payload}
        )
        self._bucket.commit()
        return vid

    # ---- 读 ----
    def head(self, oid: Any) -> str | None:
        """链头 = 不被任何 ``prev`` 指向的那条；从表中推导，不另存。"""
        rows = self._table.select(oid=str(oid))
        if not rows:
            return None
        referenced = {str(row["prev"]) for row in rows if row["prev"]}
        for row in rows:
            if str(row["id"]) not in referenced:
                return str(row["id"])
        return None

    def count(self, oid: Any) -> int:
        return len(self._table.select(oid=str(oid)))

    def history(self, oid: Any) -> list[dict[str, Any]]:
        """最新在前：``[{id, prev, at}]``。"""
        rows = {str(row["id"]): row for row in self._table.select(oid=str(oid))}
        out: list[dict[str, Any]] = []
        current = self.head(oid)
        while current is not None and current in rows:
            row = rows[current]
            out.append({"id": current, "prev": row["prev"] or None, "at": int(row["at"])})
            current = row["prev"] or None
        return out

    def patch(self, oid: Any, version: str) -> Any:
        rows = self._table.select(oid=str(oid), id=str(version))
        if not rows:
            raise ObjectNotFoundError(f"版本不存在: {oid}@{version}")
        return decode_canonical(bytes(rows[0]["payload"]))

    def state_at(self, oid: Any, codec: Codec, current_state: Any, version: str) -> Any:
        """从当前（最新）状态反向回放到指定版本（一次取回该链全部补丁，避免 N+1）。"""
        history = self.history(oid)
        payloads = {str(row["id"]): row["payload"] for row in self._table.select(oid=str(oid))}
        state = current_state
        for entry in history:
            if entry["id"] == version:
                return state
            payload = payloads.get(entry["id"])
            if payload is None:
                raise ObjectNotFoundError(f"版本补丁缺失: {oid}@{entry['id']}")
            state = codec.apply(state, decode_canonical(bytes(payload)))
        raise ObjectNotFoundError(f"版本不存在: {oid}@{version}")

    # ---- 维护 ----
    def compact(self, oid: Any, *, retention_ms: int | None = None) -> int:
        """惰性压实：从链尾（最旧）连续丢弃超出保留窗的节点。

        链顺序由 ``prev`` 决定（不依赖时间），故**只从最旧一端删连续的一段**，
        避免把中间节点挖空导致祖先不可达。
        """
        window = RETENTION_MS if retention_ms is None else retention_ms
        cutoff = now_ms() - window
        entries = self.history(oid)  # 最新在前
        removed = 0
        for entry in reversed(entries):  # 从链尾（最旧）开始
            if int(entry["at"]) >= cutoff:
                break
            self._table.delete(id=entry["id"])
            removed += 1
        if removed:
            self._bucket.commit()
        return removed


__all__ = ["RETENTION_MS", "Codec", "VersionStore", "version_id"]
