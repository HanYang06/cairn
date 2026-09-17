# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""导航结构件：标题 + 工具条 + 分组树 + 右键菜单意图。

数据来自 `TreeModel[GroupNode]`；只发意图（激活笔记 / 新建 / 右键），不写业务。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QTreeView

from ..layout import HBox, VBox
from .atoms import Divider, Label
from .structure import Toolbar

if TYPE_CHECKING:
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QWidget

    from ..models import TreeModel
    from ..rows import GroupNode


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
