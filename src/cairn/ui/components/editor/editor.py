# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`NoteEditor`：基于 `QTextEdit` + `NoteDocument` 的正文编辑器控件。

一次编辑 = 一条 `bodyChanged(body, style)` 意图；落盘由上层负责（App 去抖保存）。
撤销 / 重做 / 跨行选区 / 光标由 `QTextDocument` 原生提供。
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QTextBlockFormat, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QTextEdit, QVBoxLayout, QWidget

from ...component import Component
from .document import NoteDocument
from .formats import PARA_MAP, heading_size, paragraph_from_format

_ALIGN: dict[str, Qt.AlignmentFlag] = {
    "left": Qt.AlignmentFlag.AlignLeft,
    "center": Qt.AlignmentFlag.AlignHCenter,
    "right": Qt.AlignmentFlag.AlignRight,
}
_HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "body": 0}


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

    # ---- 工具（编辑型；行为接 QTextEdit，元数据在内核注册表）----
    def apply_tool(self, tool_id: str) -> bool:
        """执行一个编辑型工具；未识别返回 False。"""
        if tool_id in ("bold", "italic", "underline", "strike"):
            self.toggle_char_style(tool_id)
        elif tool_id.startswith("align-"):
            self.set_align(tool_id.split("-", 1)[1])
        elif tool_id in _HEADINGS:
            self.set_heading(_HEADINGS[tool_id])
        elif tool_id in ("indent-in", "indent-out"):
            self.set_indent(1 if tool_id == "indent-in" else -1)
        elif tool_id in ("bullet", "ordered"):
            self.toggle_list("ordered" if tool_id == "ordered" else "bullet")
        elif tool_id in ("quote", "code"):
            self.toggle_block(tool_id)
        elif tool_id == "clear-format":
            self.clear_char_format()
        elif tool_id == "clear-para":
            self.clear_para_format()
        else:
            return False
        return True

    def toggle_char_style(self, key: str) -> None:
        """切换行内布尔样式（bold / italic / underline / strike）。"""
        current = self._edit.currentCharFormat()
        fmt = QTextCharFormat()
        if key == "bold":
            bold = current.fontWeight() >= int(QFont.Weight.Bold)
            fmt.setFontWeight(QFont.Weight.Normal if bold else QFont.Weight.Bold)
        elif key == "italic":
            fmt.setFontItalic(not current.fontItalic())
        elif key == "underline":
            fmt.setFontUnderline(not current.fontUnderline())
        elif key == "strike":
            fmt.setFontStrikeOut(not current.fontStrikeOut())
        self._edit.mergeCurrentCharFormat(fmt)

    def set_align(self, where: str) -> None:
        """设置段落对齐。"""
        if where not in _ALIGN:
            return
        fmt = QTextBlockFormat()
        fmt.setAlignment(_ALIGN[where])
        self._merge_block(fmt)

    def set_heading(self, level: int) -> None:
        """设置标题层级（0 = 正文）。"""
        para = paragraph_from_format(self._edit.textCursor().blockFormat())
        if level:
            para["heading"] = level
        else:
            para.pop("heading", None)
        fmt = QTextBlockFormat()
        fmt.setProperty(PARA_MAP, {key: value for key, value in para.items() if key != "align"})
        self._merge_block(fmt)

        cursor = self._edit.textCursor()
        cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        char = QTextCharFormat()
        if level:
            char.setFontPointSize(heading_size(level))
            char.setFontWeight(QFont.Weight.DemiBold)
        else:
            char.setFontPointSize(float(self.theme.fs_body))
            char.setFontWeight(QFont.Weight.Normal)
        cursor.mergeCharFormat(char)
        self._edit.setTextCursor(cursor)

    def set_indent(self, delta: int) -> None:
        """缩进 / 反缩进。"""
        current = self._edit.textCursor().blockFormat().indent()
        fmt = QTextBlockFormat()
        fmt.setIndent(max(0, current + delta))
        self._merge_block(fmt)

    def toggle_list(self, kind: str) -> None:
        """切换列表（bullet / ordered）。"""
        self._patch_para("list", None if self._para().get("list") == kind else kind)

    def toggle_block(self, kind: str) -> None:
        """切换段落块（quote / code）。"""
        self._patch_para("block", None if self._para().get("block") == kind else kind)

    def clear_char_format(self) -> None:
        """清除选区（或整段）的行内样式。"""
        cursor = self._edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
        cursor.setCharFormat(QTextCharFormat())
        self._edit.setTextCursor(cursor)

    def clear_para_format(self) -> None:
        """清除段落属性。"""
        fmt = QTextBlockFormat()
        fmt.setProperty(PARA_MAP, {})
        fmt.setAlignment(Qt.AlignmentFlag.AlignLeft)
        fmt.setIndent(0)
        self._merge_block(fmt)

    def _para(self) -> dict[str, object]:
        return paragraph_from_format(self._edit.textCursor().blockFormat())

    def _patch_para(self, key: str, value: object) -> None:
        para = self._para()
        if value is None:
            para.pop(key, None)
        else:
            para[key] = value
        fmt = QTextBlockFormat()
        fmt.setProperty(PARA_MAP, {k: v for k, v in para.items() if k != "align"})
        self._merge_block(fmt)

    def _merge_block(self, fmt: QTextBlockFormat) -> None:
        cursor = self._edit.textCursor()
        cursor.mergeBlockFormat(fmt)
        self._edit.setTextCursor(cursor)


__all__ = ["NoteEditor"]
