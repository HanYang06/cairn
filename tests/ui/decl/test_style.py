# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""样式与作用域测试：令牌引用、禁硬编码、作用域继承。"""

from __future__ import annotations

import pytest

from cairn.ui.decl import Scope, StyleError, resolve_refs, token, validate_refs
from cairn.ui.theme import DARK, LIGHT


def test_token_prefix() -> None:
    assert token("accent") == "token.accent"


def test_validate_accepts_token_refs() -> None:
    validate_refs({"color": token("text"), "radius": token("radius")})


def test_validate_rejects_raw_value() -> None:
    with pytest.raises(StyleError):
        validate_refs({"color": "#FFFFFF"})


def test_validate_rejects_unknown_property() -> None:
    with pytest.raises(StyleError):
        validate_refs({"bogus": token("text")})


def test_resolve_uses_theme_value() -> None:
    assert resolve_refs(LIGHT, {"color": token("text")}) == {"color": LIGHT.text}


def test_resolve_unknown_token_errors() -> None:
    with pytest.raises(StyleError):
        resolve_refs(LIGHT, {"color": token("no-such-token")})


def test_scope_child_inherits_theme() -> None:
    root = Scope(LIGHT, name="root")
    child = root.child(name="page")
    assert child.theme is LIGHT
    assert child.parent is root


def test_scope_child_can_override_theme() -> None:
    assert Scope(LIGHT).child(theme=DARK).theme is DARK


def test_scope_resolve_style() -> None:
    resolved = Scope(LIGHT).resolve_style({"background": token("surface")})
    assert resolved == {"background": LIGHT.surface}
