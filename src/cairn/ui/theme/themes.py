# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内置主题：换主题只是换一组令牌。"""

from __future__ import annotations

from .tokens import Theme

DARK = Theme(
    name="dark",
    dark=True,
    bg="#1C1A18",
    surface="#242120",
    elevated="#2E2A26",
    border="#3A3F44",
    text="#E8E4DC",
    muted="#9A938A",
    accent="#C77B3C",
    accent_alt="#5B6E4F",
    on_accent="#1C1A18",
    selection="#3A332B",
)

LIGHT = Theme(
    name="light",
    dark=False,
    bg="#F2ECE3",
    surface="#FFFFFF",
    elevated="#EDE7DC",
    border="#D8D0C4",
    text="#2E2A26",
    muted="#7A736A",
    accent="#C77B3C",
    accent_alt="#5B6E4F",
    on_accent="#FFFFFF",
    selection="#F0E2CF",
)

BUILTIN: dict[str, Theme] = {DARK.name: DARK, LIGHT.name: LIGHT}
