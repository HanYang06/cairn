# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`NoteEditor`：基于 `QTextEdit` + `NoteDocument` 的正文编辑器控件。

一次编辑 = 一条 `bodyChanged(body, style)` 意图；落盘由上层负责（App 去抖保存）。
撤销 / 重做 / 跨行选区 / 光标由 `QTextDocument` 原生提供。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from ...component import Component
from .document import NoteDocument


class NoteEditor(Component):
    """富文本正文编辑器：装 `NoteDocument`，改动静默发 ``bodyChanged``。"""

    body_changed = Signal(list, dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._document = NoteDocument(self)
        self._edit = QTextEdit(self)
        self._edit.setObjectName("NoteEditor")
        self._edit.setAcceptRichText(False)
        self._edit.setTabChangesFocus(False)
        self._edit.setDocument(self._document)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._edit)
        self._loading = False
        self._document.contentsChanged.connect(self._on_changed)

    @property
    def edit(self) -> QTextEdit:
        """底层 `QTextEdit`。"""
        return self._edit

    @property
    def document(self) -> NoteDocument:
        """底层 `NoteDocument`。"""
        return self._document

    def load_note(self, note: Any) -> None:
        """把一篇笔记载入编辑器（不触发 ``bodyChanged``）。"""
        self._loading = True
        try:
            self._document.load_note(note)
        finally:
            self._loading = False

    def _on_changed(self) -> None:
        if self._loading:
            return
        body, style = self._document.to_body()
        self.body_changed.emit(body, style)


__all__ = ["NoteEditor"]
