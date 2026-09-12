# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import dataclasses

from cairn.core.crypto import Identity
from cairn.core.storage.manifest import Manifest, sign_manifest, verify_manifest
from cairn.core.types import ChunkRef, Cid, Oid, SpaceId


def _manifest() -> Manifest:
    return Manifest(
        oid=Oid.new(),
        space_id=SpaceId.new(),
        type="note",
        mime=None,
        size=3,
        created=1,
        updated=1,
        chunks=(ChunkRef(cid=Cid.from_digest(bytes(32)), size=3),),
        meta={"title": "t", "tags": ["a"]},
        seq=1,
        prev=None,
        author=b"",
        sig=b"",
    )


def test_sign_and_verify() -> None:
    signed = sign_manifest(_manifest(), Identity.generate())
    assert signed.author
    assert signed.sig
    assert verify_manifest(signed)


def test_unsigned_does_not_verify() -> None:
    assert not verify_manifest(_manifest())


def test_tampering_breaks_verification() -> None:
    signed = sign_manifest(_manifest(), Identity.generate())
    assert not verify_manifest(dataclasses.replace(signed, meta={"title": "changed"}))
    assert not verify_manifest(dataclasses.replace(signed, size=999))
    assert not verify_manifest(dataclasses.replace(signed, author=Identity.generate().sign_public))


def test_cbor_roundtrip_preserves_fields() -> None:
    signed = sign_manifest(_manifest(), Identity.generate())
    restored = Manifest.from_cbor(signed.to_cbor())
    assert restored == signed
