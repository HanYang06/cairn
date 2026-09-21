# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from core import Audience, ShareKind
from core.policy import is_private, parse_kind, target_audience, visible_to

_HOMEPAGE = {"kind": "homepage", "name": ""}
_COMMUNITY = {"kind": "community", "name": "Cairn 中文"}
_PERSON = {"kind": "person", "name": "韩"}


def test_private_when_no_targets() -> None:
    assert is_private([])
    assert not is_private([_HOMEPAGE])
    assert not visible_to([], Audience.PUBLIC)


def test_homepage_is_public() -> None:
    assert target_audience(ShareKind.HOMEPAGE) is Audience.PUBLIC
    for audience in Audience:
        assert visible_to([_HOMEPAGE], audience)


def test_community_and_person_scope() -> None:
    assert visible_to([_COMMUNITY], Audience.COMMUNITY)
    assert not visible_to([_COMMUNITY], Audience.PUBLIC)
    assert visible_to([_PERSON], Audience.PEER)
    assert not visible_to([_PERSON], Audience.COMMUNITY)


def test_targets_are_additive() -> None:
    shares = [_COMMUNITY, _PERSON]
    assert visible_to(shares, Audience.COMMUNITY)
    assert not visible_to(shares, Audience.PUBLIC)


def test_parse_kind_accepts_enum_and_string() -> None:
    assert parse_kind(ShareKind.HOMEPAGE) is ShareKind.HOMEPAGE
    assert parse_kind("community") is ShareKind.COMMUNITY
    assert parse_kind("nope") is None


def test_is_private_short_circuits_on_generator() -> None:
    assert is_private(iter(()))
    assert not is_private(iter([_HOMEPAGE]))
