# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""应用层：组合内核 / 领域 / `ui_tools`，按平台发布（win / linux / …）。

**只有 App 认识领域**（构造域服务、静态挂载、组装 Facet）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from feature import Note
from ui_tools.core import App, Session

from .facets import NoteFacet

if TYPE_CHECKING:
    from core import Vault
    from core.signal import Signal


class Feature:
    """静态声明的领域容器（IDE 可识别；无动态注册 / 内省）。"""

    Note: Note

    def __init__(self, vault: Vault, signal: Signal) -> None:
        self.Note = Note(vault).bind(signal)


def build(vault: Vault) -> App:
    """由库组装 UI：领域树 + `Session` + Facet。"""
    feature = Feature(vault, vault.signal)
    vault.signal.feature = feature
    session = Session(vault.signal)
    app = App(session)
    app.mount(NoteFacet(feature.Note, session))
    return app


__all__ = ["App", "Feature", "Session", "build"]
