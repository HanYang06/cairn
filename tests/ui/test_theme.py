from __future__ import annotations

from cairn.ui.theme import BUILTIN, DARK, LIGHT, build_qss


def test_themes_share_token_shape() -> None:
    assert set(DARK.as_dict()) == set(LIGHT.as_dict())
    assert DARK.name == "dark"
    assert LIGHT.name == "light"


def test_build_qss_substitutes_tokens() -> None:
    qss = build_qss(DARK)
    assert DARK.bg in qss
    assert DARK.accent in qss
    assert "$" not in qss


def test_themes_render_differently() -> None:
    assert build_qss(DARK) != build_qss(LIGHT)


def test_builtin_registry() -> None:
    assert BUILTIN["dark"] is DARK
    assert BUILTIN["light"] is LIGHT
