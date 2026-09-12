# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""序列化与落盘封帧。

- CBOR 采用确定性编码（canonical），保证同一结构字节唯一，便于签名。
- 记录格式：``ver(1B) ∥ payload``，用于块文件与清单文件。
"""

from __future__ import annotations

from typing import Any

import cbor2

from ...conf import FORMAT_VERSION
from ...types import CorruptObjectError


def encode_cbor(obj: Any) -> bytes:
    return cbor2.dumps(obj, canonical=True)


def decode_cbor(data: bytes) -> Any:
    return cbor2.loads(data)


def pack_record(payload: bytes, version: int = FORMAT_VERSION) -> bytes:
    return bytes((version,)) + payload


def unpack_record(blob: bytes) -> bytes:
    if not blob:
        raise CorruptObjectError("记录为空")
    if blob[0] != FORMAT_VERSION:
        raise CorruptObjectError(f"不支持的记录版本: {blob[0]}")
    return blob[1:]


def chunk_aad() -> bytes:
    return encode_cbor({"v": FORMAT_VERSION, "kind": "chunk"})


def manifest_aad(oid: str) -> bytes:
    return encode_cbor({"v": FORMAT_VERSION, "kind": "manifest", "oid": str(oid)})
