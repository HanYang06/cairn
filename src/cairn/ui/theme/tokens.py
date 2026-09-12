# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题令牌：所有视觉常量的唯一来源。

组件与页面不得硬编码颜色/圆角/间距，一律引用令牌；换主题 = 换一组令牌。
"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class Theme:
    """一套主题的全部令牌。"""

    name: str
    dark: bool

    bg: str
    surface: str
    elevated: str
    border: str
    text: str
    muted: str
    accent: str
    accent_alt: str
    on_accent: str
    selection: str

    radius: int = 8
    radius_card: int = 12
    spacing: int = 8
    font_family: str = "Segoe UI"
    font_size: int = 10

    def as_dict(self) -> dict[str, str]:
        return {field.name: str(getattr(self, field.name)) for field in fields(self)}
