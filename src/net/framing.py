# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""长度前缀帧：在字节流上收发一条条消息。

与传输无关：任何有 ``sendall`` / ``recv`` 的对象都能用（socket、socketpair…）。
"""

from __future__ import annotations

import struct
from typing import Any, Protocol

from core.codec import decode_cbor, encode_cbor

_HEADER = struct.Struct("!I")
MAX_FRAME_BYTES = 64 * 1024 * 1024


class FramingError(Exception):
    """帧格式错误。"""


class SocketLike(Protocol):
    def sendall(self, data: bytes, /) -> None: ...

    def recv(self, bufsize: int, /) -> bytes: ...


def send_frame(sock: SocketLike, payload: bytes) -> None:
    if len(payload) > MAX_FRAME_BYTES:
        raise FramingError("帧过大")
    sock.sendall(_HEADER.pack(len(payload)) + payload)


def _recv_exact(sock: SocketLike, size: int) -> bytes | None:
    buffer = bytearray()
    while len(buffer) < size:
        piece = sock.recv(size - len(buffer))
        if not piece:
            return None
        buffer += piece
    return bytes(buffer)


def recv_frame(sock: SocketLike) -> bytes | None:
    header = _recv_exact(sock, _HEADER.size)
    if header is None:
        return None
    (length,) = _HEADER.unpack(header)
    if length > MAX_FRAME_BYTES:
        raise FramingError("帧过大")
    return _recv_exact(sock, length)


def send_message(sock: SocketLike, message: Any) -> None:
    send_frame(sock, encode_cbor(message))


def recv_message(sock: SocketLike) -> Any | None:
    payload = recv_frame(sock)
    if payload is None:
        return None
    return decode_cbor(payload)
