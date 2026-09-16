# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""标识符类型：Oid / Cid。"""

from __future__ import annotations

import secrets
import time

from .errors import InvalidIdError

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_OID_LEN = 26
_CID_LEN = 64
_HEX_DIGITS = frozenset("0123456789abcdef")


def _encode_crockford(value: int) -> str:
    chars = [""] * _OID_LEN
    for i in range(_OID_LEN - 1, -1, -1):
        chars[i] = _CROCKFORD[value & 0x1F]
        value >>= 5
    return "".join(chars)


class Oid(str):
    """对象身份：ULID（26 字符 Crockford Base32，时间有序）。"""

    __slots__ = ()

    @classmethod
    def new(cls) -> Oid:
        ts = int(time.time() * 1000) & ((1 << 48) - 1)
        rnd = int.from_bytes(secrets.token_bytes(10), "big")
        return cls(_encode_crockford((ts << 80) | rnd))

    @classmethod
    def parse(cls, value: str) -> Oid:
        normalized = value.upper()
        if len(normalized) != _OID_LEN or normalized[0] > "7":
            raise InvalidIdError(f"非法 OID: {value!r}")
        for ch in normalized:
            if ch not in _CROCKFORD:
                raise InvalidIdError(f"非法 OID: {value!r}")
        return cls(normalized)


class Cid(str):
    """内容标识：32 字节摘要的小写十六进制。"""

    __slots__ = ()

    @classmethod
    def from_digest(cls, digest: bytes) -> Cid:
        return cls(digest.hex())

    @classmethod
    def parse(cls, value: str) -> Cid:
        if len(value) != _CID_LEN or not set(value) <= _HEX_DIGITS:
            raise InvalidIdError(f"非法 CID: {value!r}")
        return cls(value)
