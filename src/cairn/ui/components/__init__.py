# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""组件库：有行为的叶子（原子）与结构件；扩展点集中在这里。

约定：组件只吃主题令牌，不硬编码颜色 / 圆角 / 间距。布局组织器另在 `ui.layout`，
页面在 `ui.pages`。
"""

from __future__ import annotations

from ..component import Component
from .atoms import Button, Chip, Divider, Field, IconButton, Label, Section, ToggleSwitch
from .base import Panel
from .chrome import StatusBar, TitleBar
from .commandpalette import CommandPalette
from .editor import NoteDocument, NoteEditor
from .formattoolbar import FormatToolbar
from .navigator import NavigatorPanel
from .structure import ActivityBar, InspectorPanel, ListPanel, Toolbar
from .tabbar import TabBar

__all__ = [
    "ActivityBar",
    "Button",
    "Chip",
    "CommandPalette",
    "Component",
    "Divider",
    "Field",
    "FormatToolbar",
    "IconButton",
    "InspectorPanel",
    "Label",
    "ListPanel",
    "NavigatorPanel",
    "NoteDocument",
    "NoteEditor",
    "Panel",
    "Section",
    "StatusBar",
    "TabBar",
    "TitleBar",
    "ToggleSwitch",
    "Toolbar",
]
