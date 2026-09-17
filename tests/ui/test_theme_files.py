# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题包：目录扫描、加载校验、编译。"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from cairn.ui.theme import ThemeSchemaError, compile_theme, list_themes, load_theme, theme_dir

if TYPE_CHECKING:
    from pathlib import Path


def test_config_themes_discovered() -> None:
    themes = list_themes()
    assert theme_dir().is_dir()
    assert "github-light" in themes
    assert "github-dark" in themes


def test_load_theme_applies_tokens() -> None:
    theme_file = load_theme(list_themes()["github-dark"])
    assert theme_file.name == "github-dark"
    assert theme_file.dark is True
    assert theme_file.theme.bg == "#0D1117"


def test_compile_theme_includes_tokens_and_widget_rules(tmp_path: Path) -> None:
    source = tmp_path / "sample.json"
    source.write_text(
        json.dumps(
            {
                "name": "sample",
                "dark": False,
                "token": {"accent": "#123456"},
                "style": {
                    "widget.Button": {"background": "token.elevated"},
                    "widget.Button:hover": {"border_color": "token.accent"},
                },
            }
        ),
        encoding="utf-8",
    )
    qss = compile_theme(load_theme(source))
    assert "#123456" in qss
    assert '[cairnClass="Button"]' in qss
    assert ":hover" in qss


def test_unknown_path_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad.json"
    source.write_text('{"style": {"widget.Nope": {"background": "#fff"}}}', encoding="utf-8")
    with pytest.raises(ThemeSchemaError):
        load_theme(source)


def test_unknown_section_rejected(tmp_path: Path) -> None:
    source = tmp_path / "bad-section.json"
    source.write_text('{"extra": {}}', encoding="utf-8")
    with pytest.raises(ThemeSchemaError):
        load_theme(source)
