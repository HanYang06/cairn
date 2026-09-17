# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""导航结构件：标题 + 工具条 + 分组树 + 右键菜单意图。

数据来自 `TreeModel[GroupNode]`；只发意图（激活笔记 / 新建 / 右键），不写业务。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QStyle,
    QStyledItemDelegate,
    QTreeView,
)

from ..layout import HBox, VBox
from ..theme import current_theme
from .atoms import Divider, Label
from .structure import Toolbar

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint
    from PySide6.QtGui import QPainter
    from PySide6.QtWidgets import QWidget

    from ..models import TreeModel
    from ..rows import GroupNode
    from ..theme import Theme

_ROLE_KEY = int(Qt.ItemDataRole.UserRole) + 1
_ROLE_KIND = int(Qt.ItemDataRole.UserRole) + 2
_ROLE_TITLE = int(Qt.ItemDataRole.UserRole) + 3
_ROLE_PREVIEW = int(Qt.ItemDataRole.UserRole) + 4
_ROLE_UPDATED = int(Qt.ItemDataRole.UserRole) + 5
_GROUP_GLYPH = "\ue8b7"


class NavigatorDelegate(QStyledItemDelegate):
    """导航行委托：组 = 文件夹图标 + 标题；笔记 = 标题 + 预览 + 时间。"""

    def sizeHint(  # type: ignore[override]  # noqa: N802 — Qt 覆写
        self,
        _option: object,
        index: QModelIndex,
    ) -> QSize:
        kind = index.data(_ROLE_KIND)
        return QSize(200, 42 if kind == "note" else 28)

    def paint(  # type: ignore[override]
        self,
        painter: QPainter,
        option: object,
        index: QModelIndex,
    ) -> None:
        theme: Theme = current_theme()
        rect = option.rect  # type: ignore[attr-defined]
        state = option.state  # type: ignore[attr-defined]
        if state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, QColor(theme.selection))
        elif state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(rect, QColor(theme.hover))

        kind = index.data(_ROLE_KIND)
        title = str(index.data(_ROLE_TITLE) or "")
        if kind == "group":
            painter.setFont(QFont(theme.icon_font))
            painter.setPen(QColor(theme.muted))
            painter.drawText(
                rect.adjusted(2, 0, 0, 0),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                _GROUP_GLYPH,
            )
            painter.setFont(_font(theme, theme.fs_small))
            painter.setPen(QColor(theme.text))
            painter.drawText(
                rect.adjusted(22, 0, 6, 0),
                int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
                painter.fontMetrics().elidedText(
                    title, Qt.TextElideMode.ElideRight, rect.width() - 28
                ),
            )
            return

        preview = str(index.data(_ROLE_PREVIEW) or "")
        updated = str(index.data(_ROLE_UPDATED) or "")
        title_rect = QRect(rect.x() + 2, rect.y() + 5, rect.width() - 64, 17)
        updated_rect = QRect(rect.right() - 58, rect.y() + 5, 54, 17)
        preview_rect = QRect(rect.x() + 2, rect.y() + 22, rect.width() - 8, 15)

        painter.setFont(_font(theme, theme.fs_small))
        painter.setPen(QColor(theme.text))
        painter.drawText(
            title_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            painter.fontMetrics().elidedText(
                title, Qt.TextElideMode.ElideRight, title_rect.width()
            ),
        )
        painter.setPen(QColor(theme.faint))
        painter.drawText(
            updated_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight),
            updated,
        )
        painter.setPen(QColor(theme.muted))
        painter.setFont(_font(theme, theme.fs_tiny))
        painter.drawText(
            preview_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            painter.fontMetrics().elidedText(
                preview, Qt.TextElideMode.ElideRight, preview_rect.width()
            ),
        )


def _font(theme: Theme, size: int) -> QFont:
    font = QFont(theme.font_family)
    font.setPixelSize(size)
    return font


class NavigatorPanel(VBox):
    """分组导航：标题 + 工具条 + `QTreeView`；行为以意图信号外发。"""

    note_activated = Signal(str)
    new_note_requested = Signal()
    new_group_requested = Signal()
    context_requested = Signal(str, str, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent, spacing=0)
        self._model: TreeModel[GroupNode] | None = None

        header = HBox(spacing=4)
        self._title = Label("笔记", role="PanelTitle")
        self.toolbar = Toolbar()
        self.toolbar.add_action("new_note", "\ue710", tip="新建笔记")
        self.toolbar.add_action("new_group", "\ue8f4", tip="新建组")
        self.toolbar.triggered.connect(self._on_toolbar)
        header.add(self._title, stretch=1)
        header.add(self.toolbar)
        self.add(header)
        self.add(Divider())

        self._tree = QTreeView()
        self._tree.setObjectName("NavigatorTree")
        self._tree.setHeaderHidden(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._tree.activated.connect(self._on_activated)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context)
        self._tree.setItemDelegate(NavigatorDelegate(self._tree))
        self.add(self._tree, stretch=1)

    @property
    def tree(self) -> QTreeView:
        """底层树控件。"""
        return self._tree

    def set_model(self, model: TreeModel[GroupNode]) -> None:
        """绑定分组树模型；每次重载后自动展开。"""
        self._model = model
        self._tree.setModel(model)
        self._tree.expandAll()
        model.modelReset.connect(self._tree.expandAll)

    def set_title(self, text: str) -> None:
        """更新标题。"""
        self._title.text = text

    def current_node(self) -> GroupNode | None:
        """当前选中的节点（供外部动作使用）。"""
        return self._value(self._tree.currentIndex())

    def selection(self) -> list[GroupNode]:
        """当前选中的全部节点（多选批量用）。"""
        model = self._tree.selectionModel()
        if model is None:
            return []
        nodes: list[GroupNode] = []
        for index in model.selectedRows():
            node = self._value(index)
            if node is not None:
                nodes.append(node)
        return nodes

    def _value(self, index: QModelIndex) -> GroupNode | None:
        if self._model is None or not index.isValid():
            return None
        return self._model.value_at(index)

    def _on_activated(self, index: QModelIndex) -> None:
        node = self._value(index)
        if node is not None and node.kind == "note":
            self.note_activated.emit(node.key)

    def _on_context(self, pos: QPoint) -> None:
        node = self._value(self._tree.indexAt(pos))
        if node is None:
            return
        global_pos = self._tree.viewport().mapToGlobal(pos)
        self.context_requested.emit(node.kind, node.key, global_pos)

    def _on_toolbar(self, action_id: str) -> None:
        if action_id == "new_note":
            self.new_note_requested.emit()
        elif action_id == "new_group":
            self.new_group_requested.emit()


__all__ = ["NavigatorPanel"]
