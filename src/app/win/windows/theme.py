# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 壳主题：**从 `config/theme/*.json` 加载**（外观唯一真源）。

目录可用 `CAIRN_THEME_DIR` 覆盖；文件缺失时退回内置默认，保证永远能起。
"""

from __future__ import annotations

import os
from pathlib import Path

from ui_tools.core import Theme, load_theme

DEFAULT_THEME = "github-dark"

_FALLBACK_TOKENS: dict[str, str] = {
    "bg": "#0F1115",
    "surface": "#161A21",
    "elevated": "#1D222B",
    "glass": "rgba(23, 27, 34, 0.86)",
    "border": "#2A313C",
    "border_soft": "#20252E",
    "text": "#E8ECF2",
    "muted": "#98A1AD",
    "faint": "#69727E",
    "accent": "#6C9BFF",
    "accent_soft": "#232C3F",
    "ochre": "#E0A458",
    "hover": "#222833",
    "radius": "12px",
    "radius_lg": "16px",
    "radius_sm": "8px",
    "shadow_color": "#000000",
    "shadow_alpha": "110",
}

_FALLBACK_STYLES: dict[str, dict[str, str]] = {
    "widget.shell": {"background": "token.bg"},
    "widget.topbar": {"background": "token.glass", "border_radius": "token.radius_lg"},
    "widget.heading": {"color": "token.text"},
    "widget.label": {"color": "token.muted"},
    "widget.button": {"background": "transparent", "color": "token.muted"},
    "widget.stage": {"background": "token.bg", "color": "token.text"},
    "widget.taskbar": {"background": "token.surface", "color": "token.text"},
}


def theme_dir() -> Path:
    """主题目录：`CAIRN_THEME_DIR` 优先，否则仓库 `config/theme`。"""
    override = os.environ.get("CAIRN_THEME_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[4] / "config" / "theme"


def app_theme(name: str = DEFAULT_THEME) -> Theme:
    """加载命名主题文件；不存在则退回内置默认。"""
    path = theme_dir() / f"{name}.json"
    if path.exists():
        return load_theme(path)
    return Theme(_FALLBACK_TOKENS, _FALLBACK_STYLES)


__all__ = ["DEFAULT_THEME", "app_theme", "theme_dir"]
