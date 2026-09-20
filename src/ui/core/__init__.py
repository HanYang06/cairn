# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核：接入点、声明树基元、词汇表与编译管线（Qt-free）。"""

from __future__ import annotations

from .app import App, SuperLayout
from .bind import Bind, Binding
from .compile import Compiler, Translator
from .conf import Conf, ConfGroup
from .errors import LayoutError, UiError
from .facet import Facet
from .node import Node, Placed, registered_kinds
from .registry import kinds, vocabulary
from .schema import Schema
from .session import Session
from .signal import UiSignal

__all__ = [
    "App",
    "Bind",
    "Binding",
    "Compiler",
    "Conf",
    "ConfGroup",
    "Facet",
    "LayoutError",
    "Node",
    "Placed",
    "Schema",
    "Session",
    "SuperLayout",
    "Translator",
    "UiError",
    "UiSignal",
    "kinds",
    "registered_kinds",
    "vocabulary",
]
