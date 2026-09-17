# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`NoteDocument`：内核正文 ↔ `QTextDocument` 的双向映射。

- **1 行 = 1 个 block**，行 id 存在 block format 的 `LINE_ID` 用户属性 → 行身份稳定；
- 段落属性 / 行内样式 / 嵌入占位走 `formats` 的映射（扩展点集中在那里）；
- `load_note` 载入，`to_body` 回写；编辑器在两者之间随意增删改。

这样「扩一种样式 / 段落属性」只动 `formats`，不动文档与编辑器。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtGui import QTextBlock, QTextCharFormat, QTextCursor, QTextDocument

from ...domains.note.edit import is_marker, line_styles, new_id
from ...domains.note.model import Style
from .formats import (
    LINE_ID,
    OBJECT_REPLACEMENT,
    apply_paragraph,
    apply_style,
    block_base_format,
    marker_format,
    marker_from_format,
    paragraph_from_format,
    style_from_format,
)

if TYPE_CHECKING:
    from ...domains.note.edit import Line, StyleMap


class NoteDocument(QTextDocument):
    """把一篇笔记的正文装进 `QTextDocument`，并可无损回写。"""

    def load_note(self, note: Any) -> None:
        """用笔记的正文 + 样式重建文档（会清掉现有内容）。"""
        self.clear()
        style_map = note.style
        cursor = QTextCursor(self)
        cursor.beginEditBlock()
        for index, line in enumerate(note.body.text):
            if index:
                cursor.insertBlock()
            self._write_line(cursor, line, style_map)
        cursor.endEditBlock()
        self.setModified(False)

    def to_body(self) -> tuple[list[Line], StyleMap]:
        """把当前文档回写成 (行序列, 行内样式表)。"""
        body: list[Line] = []
        style_map: StyleMap = {}
        block = self.begin()
        while block.isValid():
            lid = str(block.blockFormat().property(LINE_ID) or new_id())
            entry: Line = {"id": lid, "v": self._read_value(block)}
            para = paragraph_from_format(block.blockFormat())
            if para:
                entry["p"] = para
            body.append(entry)
            ranges = self._read_inline(block)
            if ranges:
                style_map[lid] = [
                    {(start, end): Style.from_data(data) for start, end, data in ranges}
                ]
            block = block.next()
        return body, style_map

    # ---- 写 ----
    def _write_line(self, cursor: QTextCursor, line: Line, style_map: StyleMap) -> None:
        para = dict(line.get("p") or {})
        block_format = cursor.blockFormat()
        block_format.setProperty(LINE_ID, str(line["id"]))
        apply_paragraph(block_format, para)
        cursor.setBlockFormat(block_format)

        value = line["v"]
        if is_marker(value):
            kind = "canvas" if "canvas" in value else "access"
            cursor.insertText(OBJECT_REPLACEMENT, marker_format(kind, int(value[kind])))
            return

        text = str(value)
        base = block_base_format(para)
        pos = 0
        for raw_start, raw_end, style in line_styles(style_map, line):
            start = max(0, min(int(raw_start), len(text)))
            end = max(start, min(int(raw_end), len(text)))
            if start > pos:
                cursor.insertText(text[pos:start], base)
            run = QTextCharFormat(base)
            apply_style(run, style.to_data())
            cursor.insertText(text[start:end], run)
            pos = max(pos, end)
        if pos < len(text):
            cursor.insertText(text[pos:], base)

    # ---- 读 ----
    def _read_value(self, block: QTextBlock) -> Any:
        text = block.text()
        if text == OBJECT_REPLACEMENT:
            marker = marker_from_format(self._first_format(block))
            if marker is not None:
                return marker
        return text

    def _read_inline(self, block: QTextBlock) -> list[tuple[int, int, dict[str, Any]]]:
        ranges: list[tuple[int, int, dict[str, Any]]] = []
        iterator = block.begin()
        while not iterator.atEnd():
            fragment = iterator.fragment()
            if fragment.isValid():
                data = style_from_format(fragment.charFormat())
                if data:
                    start = fragment.position() - block.position()
                    ranges.append((start, start + fragment.length(), data))
            iterator += 1
        return ranges

    @staticmethod
    def _first_format(block: QTextBlock) -> QTextCharFormat:
        iterator = block.begin()
        if not iterator.atEnd() and iterator.fragment().isValid():
            return iterator.fragment().charFormat()
        return block.charFormat()


__all__ = ["NoteDocument"]
