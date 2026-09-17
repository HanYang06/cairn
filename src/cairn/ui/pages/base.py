# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""页面基类：中央内容页。页面组合结构件，不直接手搓布局。"""

from __future__ import annotations

from ..component import Component


class Page(Component):
    """中央内容页基类（笔记 / 关系 / 历史等按此派生）。"""

    abstract = True


__all__ = ["Page"]
