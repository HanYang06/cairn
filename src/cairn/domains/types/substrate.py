# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记基板：多模态片段序列。

片段是最小内容单位；文字内联，图/声/画/引用以对象引用（OID）嵌入。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...core.codec import decode_cbor, encode_cbor
from ...types import CorruptObjectError, Oid

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping


def text_fragment(text: str) -> dict[str, Any]:
    """构造内联文本片段。"""
    return {"kind": "text", "text": text}


def ref_fragment(oid: str) -> dict[str, Any]:
    """构造对象引用片段（仅 OID，无角色）。"""
    return {"kind": "ref", "oid": str(oid)}


def embed_fragment(oid: str, *, role: str = "embed", caption: str | None = None) -> dict[str, Any]:
    """构造嵌入片段（图/声/画等，可带 ``role`` 与 ``caption``）。"""
    fragment: dict[str, Any] = {"kind": "embed", "oid": str(oid), "role": role}
    if caption is not None:
        fragment["caption"] = str(caption)
    return fragment


def encode_substrate(fragments: Iterable[Mapping[str, Any]]) -> bytes:
    """把片段序列编码为确定性 CBOR 字节串。"""
    return encode_cbor([dict(fragment) for fragment in fragments])


def decode_substrate(data: bytes) -> list[dict[str, Any]]:
    """解码基板；结构不是列表时抛 ``CorruptObjectError``。"""
    raw = decode_cbor(data)
    if not isinstance(raw, list):
        raise CorruptObjectError("基板应为片段列表")
    return [dict(fragment) for fragment in raw]


def plain_text(fragments: Iterable[Mapping[str, Any]]) -> str:
    """拼接所有文本片段，返回纯文本。"""
    return "".join(str(f.get("text", "")) for f in fragments if f.get("kind") == "text")


def referenced_oids(fragments: Iterable[Mapping[str, Any]]) -> tuple[Oid, ...]:
    """按出现顺序返回片段引用到的 OID。"""
    return tuple(
        Oid.parse(str(fragment["oid"]))
        for fragment in fragments
        if fragment.get("kind") in ("ref", "embed") and "oid" in fragment
    )
