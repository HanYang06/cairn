# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""结构件：语义化组合（工具条 / 分区 / 列表面板…）。

结构件本身就是组合类型，可以再组合，深度不设限；只负责组织与联动，不写业务。
联动通过共享状态 / 控制器产生，不靠控件之间直接连线。见 `rules/references/ui-boundary.md` §6。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtWidgets import QAbstractItemView, QListView

from ..layout import HBox, VBox
from .atoms import Divider, IconButton, Label

if TYPE_CHECKING:
    from collections.abc import Callable

    from PySide6.QtWidgets import QWidget

    from ..models import ListModel


class Toolbar(HBox):
    """工具条：一组图标按钮；点击发 ``triggered(action_id)`` 意图。"""

    triggered = Signal(str)

    def __init__(self, *, spacing: int = 4, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=spacing)

    def add_action(self, action_id: str, glyph: str, *, tip: str = "") -> IconButton:
        """加一个图标动作；点击时发 ``triggered(action_id)``。"""
        button = IconButton(glyph, tip=tip, on_click=lambda: self.triggered.emit(action_id))
        self.add(button)
        return button


class ListPanel(VBox):
    """列表结构件：标题 + 工具条 + 列表；行激活发 ``activated(key)`` 意图。

    只负责展示与发意图；数据来自传入的 `ListModel`，联动由页面控制器组织。
    """

    activated = Signal(str)

    def __init__(
        self,
        title: str = "",
        *,
        key_of: Callable[[Any], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent, spacing=0)
        self._key_of = key_of
        self._model: ListModel[Any] | None = None

        header = HBox(spacing=4)
        self._title = Label(title, role="PanelTitle")
        self.toolbar = Toolbar()
        header.add(self._title, stretch=1)
        header.add(self.toolbar)
        self.add(header)
        self.add(Divider())

        self._view = QListView()
        self._view.setObjectName("ListPanelView")
        self._view.setUniformItemSizes(True)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._view.activated.connect(self._on_activated)
        self.add(self._view, stretch=1)

    @property
    def view(self) -> QListView:
        """底层列表控件。"""
        return self._view

    def set_model(self, model: ListModel[Any]) -> None:
        """绑定数据模型。"""
        self._model = model
        self._view.setModel(model)

    def set_title(self, text: str) -> None:
        """更新标题。"""
        self._title.text = text

    def _on_activated(self, index: QModelIndex) -> None:
        if self._key_of is None or self._model is None or not index.isValid():
            return
        row = self._model.row_at(index.row())
        if row is not None:
            self.activated.emit(self._key_of(row))


class ActivityBar(VBox):
    """活动栏：竖向图标条目，点击发 ``activated(item_id)`` 意图。"""

    activated = Signal(str)

    def __init__(self, *, spacing: int = 2, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=spacing)
        self._items: dict[str, IconButton] = {}

    def add_item(self, item_id: str, glyph: str, *, tip: str = "") -> IconButton:
        """加一个竖向图标条目；点击时发 ``activated(item_id)``。"""
        button = IconButton(glyph, tip=tip, on_click=lambda: self.activated.emit(item_id))
        self._items[item_id] = button
        self.add(button)
        return button

    @property
    def items(self) -> list[str]:
        """条目 id（与加入顺序一致），供页面路由用。"""
        return list(self._items)


class InspectorPanel(VBox):
    """属性检查器：标题 + 属性列表（数据来自 `ListModel`）。"""

    def __init__(self, title: str = "属性", *, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=0)
        self._title = Label(title, role="PanelTitle")
        self._view = QListView()
        self._view.setObjectName("InspectorList")
        self.add(self._title)
        self.add(Divider())
        self.add(self._view, stretch=1)

    @property
    def view(self) -> QListView:
        """底层属性列表控件。"""
        return self._view

    def set_model(self, model: ListModel[Any]) -> None:
        """绑定属性模型。"""
        self._view.setModel(model)

    def set_title(self, text: str) -> None:
        """更新标题。"""
        self._title.text = text


__all__ = ["ActivityBar", "InspectorPanel", "ListPanel", "Toolbar"]
