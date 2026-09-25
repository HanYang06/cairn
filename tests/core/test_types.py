# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import TYPE_CHECKING, Any

import pytest

from core.types import (
    Cid,
    InvalidIdError,
    ObjectInfo,
    Oid,
)
from core.types.attr import Attr

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


def test_attr_item_factory_encodes_each_element() -> None:
    attr: Attr = Attr(item=_Typed, factory=lambda: [_Typed(1), _Typed(2)])
    attr.__set_name__(_AttrsBox, "items")
    box = _AttrsBox()

    decoded = attr.__get__(box, _AttrsBox)

    # 默认值落成紧凑数据形态（与 __set__ 一致），取出来才是类型化对象
    assert box.attrs["items"] == [{"v": 1}, {"v": 2}]
    assert [item.value for item in decoded] == [1, 2]


def test_attr_item_tuple_default_is_encoded_per_element() -> None:
    # 容器默认值只放行不可变形态（#38）；元组同样逐元素编码成紧凑数据
    attr: Attr = Attr(item=_Typed, default=(_Typed(7),))
    attr.__set_name__(_AttrsBox, "items")
    box = _AttrsBox()

    assert [item.value for item in attr.__get__(box, _AttrsBox)] == [7]
    assert box.attrs["items"] == [{"v": 7}]


def test_attr_rejects_mutable_default() -> None:
    with pytest.raises(TypeError, match="factory"):
        Attr(default=[])
    with pytest.raises(TypeError, match="factory"):
        Attr(default={})


def test_attr_factory_gives_each_instance_its_own_container() -> None:
    attr: Attr = Attr(factory=list)
    attr.__set_name__(_AttrsBox, "items")
    first = _AttrsBox()
    second = _AttrsBox()

    one = attr.__get__(first, _AttrsBox)
    other = attr.__get__(second, _AttrsBox)

    assert one == []
    assert one is not other


def test_object_info_is_hashable_and_ignores_tags() -> None:
    oid = Oid.new()
    first = ObjectInfo(
        oid=oid, type="note", mime=None, size=0, created=0, updated=0, tags={"a": None}
    )
    second = ObjectInfo(
        oid=oid, type="note", mime=None, size=0, created=0, updated=0, tags={"b": None}
    )

    assert first == second  # tags 不参与比较
    assert len({first, second}) == 1  # 因而对象本身可哈希


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
