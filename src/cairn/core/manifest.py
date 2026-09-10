"""manifest 的组装、编解码、签名与验证。"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from .codec import decode_cbor, encode_cbor
from .crypto import Identity, verify_signature
from .types import (
    ChunkRef,
    Cid,
    CorruptObjectError,
    Oid,
    SpaceId,
)

MANIFEST_VERSION = 1


@dataclass(frozen=True, slots=True)
class Manifest:
    """对象清单：身份、空间、有序块表、元数据、版本链与作者签名。"""

    oid: Oid
    space_id: SpaceId
    type: str
    mime: str | None
    size: int
    created: int
    updated: int
    chunks: tuple[ChunkRef, ...]
    meta: dict[str, Any]
    seq: int
    prev: str | None
    author: bytes
    sig: bytes

    def body(self) -> dict[str, Any]:
        """除 ``sig`` 外的可签名内容。"""
        return {
            "v": MANIFEST_VERSION,
            "oid": str(self.oid),
            "space_id": str(self.space_id),
            "type": self.type,
            "mime": self.mime,
            "size": self.size,
            "created": self.created,
            "updated": self.updated,
            "chunks": [{"cid": str(ref.cid), "size": ref.size} for ref in self.chunks],
            "meta": self.meta,
            "seq": self.seq,
            "prev": self.prev,
            "author": self.author.hex(),
        }

    def to_cbor(self) -> bytes:
        data = self.body()
        data["sig"] = self.sig.hex()
        return encode_cbor(data)

    @classmethod
    def from_cbor(cls, data: bytes) -> Manifest:
        raw = decode_cbor(data)
        try:
            return cls(
                oid=Oid.parse(raw["oid"]),
                space_id=SpaceId.parse(raw["space_id"]),
                type=raw["type"],
                mime=raw.get("mime"),
                size=raw["size"],
                created=raw["created"],
                updated=raw["updated"],
                chunks=tuple(
                    ChunkRef(cid=Cid.parse(item["cid"]), size=item["size"])
                    for item in raw["chunks"]
                ),
                meta=raw.get("meta") or {},
                seq=raw["seq"],
                prev=raw.get("prev"),
                author=bytes.fromhex(raw["author"]),
                sig=bytes.fromhex(raw["sig"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CorruptObjectError("manifest 解析失败") from exc


def sign_manifest(manifest: Manifest, identity: Identity) -> Manifest:
    body = manifest.body()
    body["author"] = identity.sign_public.hex()
    signature = identity.sign(encode_cbor(body))
    return replace(manifest, author=identity.sign_public, sig=signature)


def verify_manifest(manifest: Manifest) -> bool:
    if not manifest.sig:
        return False
    return verify_signature(manifest.author, manifest.sig, encode_cbor(manifest.body()))
