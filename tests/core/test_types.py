# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import TYPE_CHECKING, Any

import pytest

from core.conf.core import FORMAT_VERSION, VAULT_META_CONTEXT
from core.types import (
    Attr,
    Cid,
    InvalidIdError,
    ObjectInfo,
    Oid,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

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


def test_cid_from_digest_rejects_wrong_length() -> None:
    with pytest.raises(InvalidIdError):
        Cid.from_digest(b"short")


class _AttrsBox:
    def __init__(self) -> None:
        self.attrs: dict[str, object] = {}


class _Point:
    def __init__(self, x: int) -> None:
        self.x = x


class _Typed:
    """最小类型化值：带 ``to_data`` / ``from_data``，模拟 ``Signature`` 这类 ``item`` 元素。"""

    def __init__(self, value: int) -> None:
        self.value = value

    def to_data(self) -> dict[str, int]:
        return {"v": self.value}

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> _Typed:
        return cls(int(data["v"]))


def test_attr_item_decode_rejects_non_mapping() -> None:
    attr: Attr = Attr(item=_Point)
    attr.__set_name__(_AttrsBox, "p")
    box = _AttrsBox()
    box.attrs["p"] = [5]
    with pytest.raises(TypeError, match="映射形态"):
        _ = attr.__get__(box, _AttrsBox)


def test_attr_item_default_encodes_each_element() -> None:
    attr: Attr = Attr(item=_Typed, default=[_Typed(1), _Typed(2)])
    attr.__set_name__(_AttrsBox, "items")
    box = _AttrsBox()

    decoded = attr.__get__(box, _AttrsBox)

    # 默认值落成紧凑数据形态（与 __set__ 一致），取出来才是类型化对象
    assert box.attrs["items"] == [{"v": 1}, {"v": 2}]
    assert [item.value for item in decoded] == [1, 2]


def test_attr_item_factory_result_is_normalized() -> None:
    attr: Attr = Attr(item=_Typed, factory=lambda: [_Typed(7)])
    attr.__set_name__(_AttrsBox, "items")
    box = _AttrsBox()

    _ = attr.__get__(box, _AttrsBox)

    assert box.attrs["items"] == [{"v": 7}]


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


def test_vault_meta_context_tracks_format_version() -> None:
    assert f"cairn/v{FORMAT_VERSION}/vault/meta" == VAULT_META_CONTEXT
