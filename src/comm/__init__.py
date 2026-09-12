# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""网络层（P2P/Server 通信底层）。

P0：内容寻址池之间的最小互联——按 CID/OID 交换密文块与对象信封。
"""

from __future__ import annotations

from .framing import FramingError, recv_message, send_message
from .peer import BlobSource, ChunkServer, PeerClient
from .protocol import (
    OP_CHUNK,
    OP_ERROR,
    OP_HEAD,
    OP_HEADS,
    OP_MISS,
    OP_WANT,
    chunk,
    error,
    head_request,
    head_response,
    miss,
    want,
)

__all__ = [
    "OP_CHUNK",
    "OP_ERROR",
    "OP_HEAD",
    "OP_HEADS",
    "OP_MISS",
    "OP_WANT",
    "BlobSource",
    "ChunkServer",
    "FramingError",
    "PeerClient",
    "chunk",
    "error",
    "head_request",
    "head_response",
    "miss",
    "recv_message",
    "send_message",
    "want",
]
