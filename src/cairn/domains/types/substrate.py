"""笔记基板：多模态片段序列。

片段是最小内容单位；文字内联，图/声/画/引用以对象引用（OID）嵌入。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from ...core.codec import decode_cbor, encode_cbor
from ...types import CorruptObjectError, Oid


def text_fragment(text: str) -> dict[str, Any]:
    return {"kind": "text", "text": text}


def ref_fragment(oid: str) -> dict[str, Any]:
    return {"kind": "ref", "oid": str(oid)}


def embed_fragment(oid: str, *, role: str = "embed", caption: str | None = None) -> dict[str, Any]:
    fragment: dict[str, Any] = {"kind": "embed", "oid": str(oid), "role": role}
    if caption is not None:
        fragment["caption"] = str(caption)
    return fragment


def encode_substrate(fragments: Iterable[Mapping[str, Any]]) -> bytes:
    return encode_cbor([dict(fragment) for fragment in fragments])


def decode_substrate(data: bytes) -> list[dict[str, Any]]:
    raw = decode_cbor(data)
    if not isinstance(raw, list):
        raise CorruptObjectError("基板应为片段列表")
    return [dict(fragment) for fragment in raw]


def plain_text(fragments: Iterable[Mapping[str, Any]]) -> str:
    return "".join(str(f.get("text", "")) for f in fragments if f.get("kind") == "text")


def referenced_oids(fragments: Iterable[Mapping[str, Any]]) -> tuple[Oid, ...]:
    return tuple(
        Oid.parse(str(fragment["oid"]))
        for fragment in fragments
        if fragment.get("kind") in ("ref", "embed") and "oid" in fragment
    )
