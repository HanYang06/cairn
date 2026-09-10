"""核心值类型与异常。

本模块不产生副作用（除生成随机 ID 外），是整个 core 的公共词汇表。
"""

from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from enum import Enum

_CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_OID_LEN = 26
_CID_LEN = 64
_HEX_DIGITS = frozenset("0123456789abcdef")


class CairnError(Exception):
    """所有 core 异常的基类。"""


class InvalidIdError(CairnError, ValueError):
    """标识符格式非法。"""


class AuthError(CairnError):
    """认证或解密失败。"""


class VaultError(CairnError):
    """库级错误。"""


class VaultLockedError(VaultError):
    """库处于锁定状态。"""


class ObjectNotFoundError(CairnError):
    """对象不存在。"""


class SpaceNotFoundError(CairnError):
    """空间不存在。"""


class CorruptObjectError(CairnError):
    """对象数据损坏或校验失败。"""


def now_ms() -> int:
    """当前 Unix 毫秒时间戳。"""
    return int(time.time() * 1000)


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


class SpaceId(str):
    """空间身份，同样采用 ULID。"""

    __slots__ = ()

    @classmethod
    def new(cls) -> SpaceId:
        return cls(Oid.new())

    @classmethod
    def parse(cls, value: str) -> SpaceId:
        return cls(Oid.parse(value))


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


class Visibility(Enum):
    """可见性档位，决定密钥分发与去重范围。"""

    PRIVATE = "private"
    COMMUNAL = "communal"
    PUBLIC = "public"
    DIRECT = "direct"


@dataclass(frozen=True, slots=True)
class ChunkRef:
    """清单中对一个块的引用。"""

    cid: Cid
    size: int


@dataclass(frozen=True, slots=True)
class ObjectInfo:
    """对象的元数据视图，不含其内容。"""

    oid: Oid
    space_id: SpaceId
    type: str
    mime: str | None
    size: int
    created: int
    updated: int
    title: str | None = None
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Space:
    """空间：策略与密钥的载体。"""

    space_id: SpaceId
    name: str
    visibility: Visibility
    created: int
