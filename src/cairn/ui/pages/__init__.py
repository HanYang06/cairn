# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""页面层：由结构件组装，不写样式细节。"""

from __future__ import annotations

from .base import Page
from .history import HistoryPage
from .relations import RelationsPage
from .search import SearchPage
from .tags import TagsPage

__all__ = ["HistoryPage", "Page", "RelationsPage", "SearchPage", "TagsPage"]
