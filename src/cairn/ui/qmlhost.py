# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""QML 岛承载器：包一层 `QQuickWidget`，把「嵌一块 QML」变简单。

宿主只认这个 `QmlView` 壳：给源码 + 类型化上下文即可；岛内不持应用状态、不碰 Vault。
见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget

from .components import Component

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


class QmlView(Component):
    """承载一个 QML 岛：源码 + 上下文，其余交给宿主。"""

    def __init__(
        self,
        source: str | Path,
        *,
        context: Mapping[str, object] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = QQuickWidget(self)
        self._view.setObjectName("QmlView")
        self._view.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        for name, value in (context or {}).items():
            self._view.rootContext().setContextProperty(name, value)
        self._view.setSource(QUrl.fromLocalFile(str(source)))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    @property
    def view(self) -> QQuickWidget:
        """底层 `QQuickWidget`。"""
        return self._view

    def root_object(self) -> QObject | None:
        """QML 根对象（尚未加载则 None）。"""
        return self._view.rootObject()

    def set_context_property(self, name: str, value: object) -> None:
        """注入 / 更新一个 QML 上下文属性。"""
        self._view.rootContext().setContextProperty(name, value)


__all__ = ["QmlView"]
