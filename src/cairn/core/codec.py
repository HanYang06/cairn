# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""CBOR 编解码（确定性）。

同一结构编码为唯一字节串，服务哈希、去重与跨层传输。
"""

from __future__ import annotations

from typing import Any

import cbor2


def encode_cbor(obj: Any) -> bytes:
    return cbor2.dumps(obj, canonical=True)


def decode_cbor(data: bytes) -> Any:
    return cbor2.loads(data)


__all__ = ["decode_cbor", "encode_cbor"]
