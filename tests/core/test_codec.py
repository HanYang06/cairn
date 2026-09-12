from __future__ import annotations

import pytest

from cairn.core.storage.codec import (
    FORMAT_VERSION,
    chunk_aad,
    decode_cbor,
    encode_cbor,
    manifest_aad,
    pack_record,
    unpack_record,
)
from cairn.core.types import CorruptObjectError


def test_encode_cbor_is_deterministic() -> None:
    assert encode_cbor({"b": 2, "a": 1}) == encode_cbor({"a": 1, "b": 2})
    assert decode_cbor(encode_cbor({"a": [1, 2], "b": "x"})) == {"a": [1, 2], "b": "x"}


def test_pack_unpack_roundtrip() -> None:
    assert unpack_record(pack_record(b"payload")) == b"payload"


def test_unpack_rejects_empty_and_bad_version() -> None:
    with pytest.raises(CorruptObjectError):
        unpack_record(b"")
    with pytest.raises(CorruptObjectError):
        unpack_record(bytes((FORMAT_VERSION + 1,)) + b"x")


def test_aad_builders() -> None:
    assert isinstance(chunk_aad(), bytes)
    assert isinstance(manifest_aad("01ABC"), bytes)
    assert chunk_aad() != manifest_aad("01ABC")
