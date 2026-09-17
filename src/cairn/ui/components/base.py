# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""部件基类：`Component`（薄基类）+ `Panel`（侧栏）+ `Page`（中央页）。

约定见 `rules/references/ui-boundary.md`：样式只取令牌、`objectName` 必填、
部件只发意图信号、业务不落在控件里。
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from ..signal import Subscription
from ..theme import Theme, current_theme

if TYPE_CHECKING:
    from collections.abc import Callable


class Component(QWidget):
    """所有 UI 部件的薄基类：统一令牌访问、命名约定与生命周期安全订阅。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._watchers: list[tuple[Any, Any]] = []
        self.destroyed.connect(self._cancel_watchers)
        if not self.objectName():
            self.setObjectName(type(self).__name__)

    @property
    def theme(self) -> Theme:
        """当前主题令牌；组件样式一律取自这里，不硬编码。"""
        return current_theme()

    def watch(self, source: Any, slot: Callable[..., None]) -> None:
        """订阅一个信号（Qt 信号或 `ui.signal.Signal`）；控件销毁时自动退订。"""
        connection = source.connect(slot)
        self._watchers.append((source, connection))

    def _cancel_watchers(self, *_args: object) -> None:
        for source, connection in self._watchers:
            if isinstance(connection, Subscription):
                connection.cancel()
            else:
                with suppress(Exception):
                    source.disconnect(connection)
        self._watchers.clear()


class Panel(Component):
    """可停靠侧栏内容的容器：标题 + 内容区。"""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = QLabel(title)
        self._title.setObjectName("PanelTitle")
        self._body = QWidget()
        self._body.setObjectName("PanelBody")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._title)
        layout.addWidget(self._body, 1)

    @property
    def body(self) -> QWidget:
        """内容容器；调用方把实际控件加进它的布局。"""
        return self._body

    def set_title(self, text: str) -> None:
        """更新标题栏文字。"""
        self._title.setText(text)


class Page(Component):
    """中央内容页基类（笔记 / 关系 / 历史等按此派生）。"""


__all__ = ["Component", "Page", "Panel"]
