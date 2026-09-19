# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""把内容寻址池暴露成可被连的节点，以及拉取方。

P0：盲服密文块——无需密钥即可提供，机密性由内容加密保证。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from . import protocol as proto
from .framing import recv_message, send_message

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from core.types import Cid, Oid


class BlobSource(Protocol):
    """只按 CID/OID 提供字节的对象池视图。"""

    def read_chunk(self, cid: str, /) -> bytes: ...

    def read_object(self, oid: str, /) -> bytes: ...


class ChunkServer:
    """处理单条连接的请求，按 want/head 应答。"""

    def __init__(self, source: BlobSource) -> None:
        self._source = source

    def serve_connection(self, sock: Any) -> None:
        while True:
            message = recv_message(sock)
            if message is None:
                return
            for reply in self._handle(message):
                send_message(sock, reply)

    def _handle(self, message: dict[str, Any]) -> Iterator[dict[str, Any]]:
        op = message.get("op")
        if op == proto.OP_WANT:
            yield from self._serve_want(message)
        elif op == proto.OP_HEAD:
            yield self._serve_head(message)
        else:
            yield proto.error(f"未知请求: {op!r}")

    def _serve_want(self, message: dict[str, Any]) -> Iterator[dict[str, Any]]:
        for cid in message.get("cids", []):
            try:
                blob = self._source.read_chunk(cid)
            except FileNotFoundError:
                yield proto.miss(cid)
            else:
                yield proto.chunk(cid, blob)

    def _serve_head(self, message: dict[str, Any]) -> dict[str, Any]:
        oid = message.get("oid", "")
        try:
            envelope = self._source.read_object(oid)
        except FileNotFoundError:
            return proto.error(f"对象不存在: {oid}")
        return proto.head_response(oid, envelope)


class PeerClient:
    """向对端发起请求的客户端。"""

    def __init__(self, sock: Any) -> None:
        self._sock = sock

    def fetch_chunks(self, cids: Iterable[Cid | str]) -> dict[str, bytes]:
        wanted = [str(cid) for cid in cids]
        send_message(self._sock, proto.want(wanted))
        received: dict[str, bytes] = {}
        for _ in wanted:
            reply = recv_message(self._sock)
            if reply is None:
                raise ConnectionError("连接在对端应答前关闭")
            if reply.get("op") == proto.OP_CHUNK:
                received[reply["cid"]] = reply["blob"]
        return received

    def fetch_object(self, oid: Oid | str) -> bytes | None:
        send_message(self._sock, proto.head_request(oid))
        reply = recv_message(self._sock)
        if reply is None:
            raise ConnectionError("连接在对端应答前关闭")
        if reply.get("op") == proto.OP_HEADS:
            envelope: bytes = reply["envelope"]
            return envelope
        return None
