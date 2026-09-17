# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题 schema：注册表 → 可写路径的自动派生与校验。"""

from __future__ import annotations

import pytest

from cairn.ui.components import Component
from cairn.ui.theme import ThemeSchemaError, schema_paths, selector_paths, validate_path


def test_registry_excludes_abstract_bases() -> None:
    registry = Component.registry()
    assert "Button" in registry
    assert "Label" in registry
    assert "Box" not in registry  # 抽象基类不入册
    assert "Page" not in registry


def test_schema_derives_tokens_and_widget_paths() -> None:
    paths = schema_paths()
    assert "token.accent" in paths
    assert "widget.Button.background" in paths
    assert "widget.Button.hover.background" in paths
    assert "widget.Label.background" in paths


def test_validate_accepts_known_paths() -> None:
    validate_path("token.bg")
    validate_path("widget.Label.color")
    validate_path("widget.Button.pressed.background")


def test_selector_paths_are_dotted_targets() -> None:
    selectors = selector_paths()
    assert "widget.Button" in selectors
    assert "widget.Button:hover" in selectors
    assert "widget.Label" in selectors


def test_validate_rejects_unknown_path() -> None:
    with pytest.raises(ThemeSchemaError):
        validate_path("widget.Nope.background")
