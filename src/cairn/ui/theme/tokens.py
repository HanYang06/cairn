# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题令牌：所有视觉常量的**唯一真源**。

组件与页面不得硬编码颜色 / 圆角 / 间距，一律引用令牌；换主题 = 换一组令牌。
色盘参照 GitHub Primer，圆角 / 阴影参照苹果；与 QML 岛共用这一组值（QML 侧需同步 / 生成）。
"""

from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True, slots=True)
class Theme:
    """一套主题的全部令牌。"""

    name: str
    dark: bool

    # ===== palette（GitHub Primer）=====
    bg: str
    chrome: str
    surface: str
    elevated: str
    border: str
    border_strong: str
    border_faint: str
    text: str
    muted: str
    faint: str
    accent: str
    accent_alt: str
    accent_text: str
    selection: str
    hover: str
    danger: str

    # ===== radius =====
    radius_sm: int = 6
    radius: int = 8
    radius_lg: int = 10
    radius_xl: int = 12

    # ===== spacing =====
    space_xs: int = 4
    space_sm: int = 8
    space_md: int = 12
    space_lg: int = 16
    space_xl: int = 24

    # ===== typography（中英统一等宽）=====
    font_family: str = "Sarasa Mono SC"
    icon_font: str = "Segoe MDL2 Assets"
    mono_font: str = "Sarasa Mono SC"
    fs_tiny: int = 11
    fs_small: int = 12
    fs_body: int = 13
    fs_large: int = 15
    fs_title: int = 22

    # ===== layout metrics =====
    title_bar_h: int = 38
    activity_w: int = 48
    side_bar_w: int = 264
    tab_bar_h: int = 36
    status_h: int = 24

    # ===== motion =====
    dur_fast: int = 120
    dur_base: int = 180
    dur_slow: int = 260
    easing: str = "outQuad"
    reduce_motion: bool = False

    # ===== shadow（QSS 无阴影，编译成代码侧效果）=====
    shadow_color: str = "#14000000"
    shadow_blur: int = 24
    shadow_offset: int = 4

    def as_dict(self) -> dict[str, str]:
        """扁平化为字符串字典，供 QSS 模板替换。"""
        return {field.name: str(getattr(self, field.name)) for field in fields(self)}


__all__ = ["Theme"]
