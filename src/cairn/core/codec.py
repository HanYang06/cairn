# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""CBOR 编解码（确定性）。

同一结构编码为唯一字节串，服务哈希、去重与跨层传输。
"""

from __future__ import annotations

from typing import Any

import cbor2


def encode_cbor(obj: Any) -> bytes:
    """把对象编码为确定性 CBOR 字节串（canonical，键序稳定）。"""
    return cbor2.dumps(obj, canonical=True)


def decode_cbor(data: bytes) -> Any:
    """把 CBOR 字节串解码为 Python 对象。"""
    return cbor2.loads(data)


__all__ = ["decode_cbor", "encode_cbor"]
