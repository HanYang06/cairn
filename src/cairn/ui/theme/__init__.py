# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题系统：令牌 + 内置主题 + QSS 渲染 + 当前主题状态。

本包不依赖 Qt，便于测试与复用；把 QSS 挂到应用上由 ``cairn.ui.theme.manager`` 负责。
"""

from __future__ import annotations

from .loader import ThemeFile, list_themes, load_theme, repo_root, theme_dir
from .qss import build_qss, build_widget_qss, compile_theme
from .schema import (
    META_KEYS,
    SCHEMA_ID,
    ThemeSchemaError,
    json_schema,
    schema_paths,
    selector_paths,
    token_paths,
    validate_path,
    widget_paths,
)
from .state import current_theme, set_current_theme
from .themes import BUILTIN, DARK, LIGHT
from .tokens import Theme

__all__ = [
    "BUILTIN",
    "DARK",
    "LIGHT",
    "META_KEYS",
    "SCHEMA_ID",
    "Theme",
    "ThemeFile",
    "ThemeSchemaError",
    "build_qss",
    "build_widget_qss",
    "compile_theme",
    "current_theme",
    "json_schema",
    "list_themes",
    "load_theme",
    "repo_root",
    "schema_paths",
    "selector_paths",
    "set_current_theme",
    "theme_dir",
    "token_paths",
    "validate_path",
    "widget_paths",
]
