# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""签名：**一套复合结构（一组字段）**，不是一段串。

它由若干字段组成，字段齐全即可自包含地验证：

    alg       算法位（当前 ``b3`` = 哈希链；日后可换 ``ed25519``，格式不破）
    author    署名者
    created   生成时间（unix ms）
    subject   被保护对象的内容签名（如 ``body.hash``）——原始结构据此可找回
    prev      上一个签名（链，跟着走）
    value     由以上字段推出的校验值（自包含、改任一字段即对不上）

两种含义：
- **创作签名**：创建时生成，锁死不变，``subject`` 指向创建时的 ``body_hash``；
  原始结构永远可通过 ``subject`` 找回。
- **变更签名**：非原作者改动时追加，``prev`` 指向上一签名（多作者协作时才需要，模型预留）。
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any

from blake3 import blake3

from core.storage import canonical
from core.types import now_ms

FORMAT = "cn1"


def _digest(alg: str, author: str, created: int, prev: str, subject: str) -> str:
    payload = {
        "alg": alg,
        "author": author,
        "created": int(created),
        "prev": prev,
        "subject": subject,
    }
    return blake3(canonical(payload)).hexdigest()


@dataclass(frozen=True, slots=True)
class Signature:
    """复合签名：字段 + 由字段推出的校验值。"""

    alg: str = "b3"
    author: str = ""
    created: int = 0
    subject: str = ""
    prev: str = ""
    value: str = ""

    def to_data(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_data(cls, data: Any) -> Signature:
        """由落盘数据还原；异形输入不崩，交由 ``verify`` 判定真伪。"""
        if data is None:
            return cls()
        if isinstance(data, str):  # 兼容旧的弱签名串
            return cls(value=str(data))
        if not isinstance(data, Mapping):
            raise TypeError(f"签名数据必须是映射，得到 {type(data).__name__}")
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)

    @classmethod
    def create(
        cls,
        *,
        author: str,
        subject: str,
        prev: str = "",
        alg: str = "b3",
        created: int | None = None,
    ) -> Signature:
        moment = now_ms() if created is None else int(created)
        return cls(
            alg=alg,
            author=author,
            created=moment,
            subject=subject,
            prev=prev,
            value=_digest(alg, author, moment, prev, subject),
        )

    def verify(self) -> bool:
        """自校验：重算 value，对不上说明字段被改过（脏数据一律判假，不抛异常）。"""
        try:
            expected = _digest(self.alg, self.author, self.created, self.prev, self.subject)
        except (TypeError, ValueError):
            return False
        return self.value == expected

    def encoded(self) -> str:
        """落成人可读的复合串（自包含）。"""
        return ".".join(
            (FORMAT, self.alg, self.author, str(self.created), self.prev, self.subject, self.value)
        )


__all__ = ["FORMAT", "Signature"]
