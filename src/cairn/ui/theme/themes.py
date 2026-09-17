# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内置主题：换主题只是换一组令牌。色值对齐 `CairnTheme.qml`（GitHub Primer）。"""

from __future__ import annotations

from .tokens import Theme

DARK = Theme(
    name="dark",
    dark=True,
    bg="#0D1117",
    chrome="#010409",
    surface="#0D1117",
    elevated="#161B22",
    border="#30363D",
    border_strong="#484F58",
    border_faint="#21262D",
    text="#E6EDF3",
    muted="#8B949E",
    faint="#6E7681",
    accent="#2F81F7",
    accent_alt="#3FB950",
    accent_text="#FFFFFF",
    selection="#1F6FEB",
    hover="#161B22",
    danger="#F85149",
)

LIGHT = Theme(
    name="light",
    dark=False,
    bg="#FFFFFF",
    chrome="#F6F8FA",
    surface="#FFFFFF",
    elevated="#FFFFFF",
    border="#D0D7DE",
    border_strong="#AFB8C1",
    border_faint="#E6EAEF",
    text="#1F2328",
    muted="#656D76",
    faint="#6E7781",
    accent="#0969DA",
    accent_alt="#1A7F37",
    accent_text="#FFFFFF",
    selection="#DDF4FF",
    hover="#F3F4F6",
    danger="#CF222E",
)

BUILTIN: dict[str, Theme] = {DARK.name: DARK, LIGHT.name: LIGHT}

__all__ = ["BUILTIN", "DARK", "LIGHT"]
