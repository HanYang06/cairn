# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from cairn.core import Audience, Visibility
from cairn.core.policy import can_share


def test_private_only_self() -> None:
    assert can_share(Visibility.PRIVATE, Audience.SELF)
    for audience in (Audience.PEER, Audience.COMMUNITY, Audience.PUBLIC):
        assert not can_share(Visibility.PRIVATE, audience)


def test_public_shares_to_all() -> None:
    for audience in Audience:
        assert can_share(Visibility.PUBLIC, audience)


def test_direct_and_communal() -> None:
    assert can_share(Visibility.DIRECT, Audience.PEER)
    assert not can_share(Visibility.DIRECT, Audience.PUBLIC)
    assert can_share(Visibility.COMMUNAL, Audience.COMMUNITY)
    assert not can_share(Visibility.COMMUNAL, Audience.PUBLIC)
