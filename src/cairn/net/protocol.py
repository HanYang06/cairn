"""Cairn 网络数据面消息。

最小协议：只要"我要这些 CID"能被回答，内容寻址池就能互联（见 network.md）。
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ..core.types import Cid, Oid

OP_WANT = "want"
OP_CHUNK = "chunk"
OP_MISS = "miss"
OP_HEAD = "head"
OP_HEADS = "heads"
OP_ERROR = "error"


def want(cids: Iterable[Cid | str]) -> dict[str, Any]:
    return {"op": OP_WANT, "cids": [str(cid) for cid in cids]}


def chunk(cid: Cid | str, blob: bytes) -> dict[str, Any]:
    return {"op": OP_CHUNK, "cid": str(cid), "blob": blob}


def miss(cid: Cid | str) -> dict[str, Any]:
    return {"op": OP_MISS, "cid": str(cid)}


def head_request(oid: Oid | str) -> dict[str, Any]:
    return {"op": OP_HEAD, "oid": str(oid)}


def head_response(oid: Oid | str, envelope: bytes) -> dict[str, Any]:
    return {"op": OP_HEADS, "oid": str(oid), "envelope": envelope}


def error(message: str) -> dict[str, Any]:
    return {"op": OP_ERROR, "message": message}
