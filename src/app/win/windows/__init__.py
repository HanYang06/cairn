# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 窗口层：根壳 `CairnApp`、领域 Facet 与主题加载。"""

from __future__ import annotations

from .app import CairnApp
from .notes import NoteFacet
from .theme import DEFAULT_THEME, app_theme, theme_dir

__all__ = ["DEFAULT_THEME", "CairnApp", "NoteFacet", "app_theme", "theme_dir"]
