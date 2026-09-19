# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from core.types import (
    Cid,
    InvalidIdError,
    ObjectInfo,
    Oid,
)

_CROCKFORD = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ")


def test_oid_new_shape() -> None:
    oid = Oid.new()
    assert len(oid) == 26
    assert set(oid) <= _CROCKFORD
    assert oid[0] <= "7"


def test_oid_new_is_unique() -> None:
    oids = {Oid.new() for _ in range(1000)}
    assert len(oids) == 1000
    for oid in oids:
        assert Oid.parse(oid) == oid


def test_oid_parse_roundtrip() -> None:
    oid = Oid.new()
    assert Oid.parse(oid) == oid
    assert Oid.parse(str(oid).lower()) == oid


@pytest.mark.parametrize(
    "bad",
    ["", "SHORT", "0" * 25, "8" + "0" * 25, "0" * 25 + "!", "0" * 25 + "I"],
)
def test_oid_parse_rejects(bad: str) -> None:
    with pytest.raises(InvalidIdError):
        Oid.parse(bad)


def test_cid_from_digest_and_parse() -> None:
    digest = bytes(range(32))
    cid = Cid.from_digest(digest)
    assert len(cid) == 64
    assert Cid.parse(str(cid)) == cid


def test_cid_parse_rejects() -> None:
    with pytest.raises(InvalidIdError):
        Cid.parse("abc")
    with pytest.raises(InvalidIdError):
        Cid.parse("g" * 64)


def test_value_types_are_frozen() -> None:
    info = ObjectInfo(
        oid=Oid.new(),
        type="note",
        mime=None,
        size=0,
        created=0,
        updated=0,
    )
    with pytest.raises(FrozenInstanceError):
        info.size = 1  # type: ignore[misc]
