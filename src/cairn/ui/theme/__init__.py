# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题系统：令牌 + 内置主题 + QSS 渲染 + 当前主题状态。

本包不依赖 Qt，便于测试与复用；把 QSS 挂到应用上由 ``cairn.ui.theme.manager`` 负责。
"""

from __future__ import annotations

from .qss import build_qss
from .state import current_theme, set_current_theme
from .themes import BUILTIN, DARK, LIGHT
from .tokens import Theme

__all__ = [
    "BUILTIN",
    "DARK",
    "LIGHT",
    "Theme",
    "build_qss",
    "current_theme",
    "set_current_theme",
]
