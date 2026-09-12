# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题系统：令牌 + 内置主题 + QSS 渲染。

本包不依赖 Qt，便于测试与复用；应用主题由 ``cairn.ui.theme.manager`` 负责。
"""

from __future__ import annotations

from .qss import build_qss
from .themes import BUILTIN, DARK, LIGHT
from .tokens import Theme

__all__ = ["BUILTIN", "DARK", "LIGHT", "Theme", "build_qss"]
