# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""编辑器扩展点：内核正文 ↔ `QTextFormat` 的映射。

扩展方式（有界但可扩）：
- **段落**：整块 `p` 存进 block format 的一个用户属性（`PARA_MAP`），任何键都无损往返；
  `align` / `level` 另做视觉映射。
- **行内**：`Style` 字段 ↔ `QTextCharFormat` 属性，一条映射一行。
- **嵌入**：占位存 `kind` / `index` 用户属性，日后可接 `QTextObjectInterface`。

新增一种样式 / 段落属性，只需在这里加映射，不动编辑器与文档。
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QTextBlockFormat, QTextCharFormat, QTextFormat

from ...theme import current_theme

if TYPE_CHECKING:
    from ....domains.note.model import Style

_USER = int(QTextFormat.Property.UserProperty)
LINE_ID = _USER + 1
MARKER_KIND = _USER + 2
MARKER_INDEX = _USER + 3
PARA_MAP = _USER + 9

OBJECT_REPLACEMENT = "\ufffc"

_ALIGN_TO_QT: dict[str, Qt.AlignmentFlag] = {
    "left": Qt.AlignmentFlag.AlignLeft,
    "center": Qt.AlignmentFlag.AlignHCenter,
    "right": Qt.AlignmentFlag.AlignRight,
}
_MARKER_KINDS = ("canvas", "access")


# ---- 段落 ----
def apply_paragraph(fmt: QTextBlockFormat, para: Mapping[str, Any]) -> None:
    """把段落属性写进 block format（`align` 视觉映射，其余整块存用户属性）。"""
    align = para.get("align")
    if align in _ALIGN_TO_QT:
        fmt.setAlignment(_ALIGN_TO_QT[align])
    level = para.get("level")
    if isinstance(level, int) and level > 0:
        fmt.setIndent(level)
    rest = {key: value for key, value in para.items() if key != "align"}
    if rest:
        fmt.setProperty(PARA_MAP, rest)


def paragraph_from_format(fmt: QTextBlockFormat) -> dict[str, Any]:
    """从 block format 还原段落属性。"""
    raw = fmt.property(PARA_MAP)
    para: dict[str, Any] = dict(raw) if isinstance(raw, Mapping) else {}
    alignment = fmt.alignment()
    if alignment & Qt.AlignmentFlag.AlignHCenter:
        para["align"] = "center"
    elif alignment & Qt.AlignmentFlag.AlignRight:
        para["align"] = "right"
    return para


def heading_size(heading: int) -> float:
    """标题字号：由主题令牌推出。"""
    theme = current_theme()
    if heading == 1:
        return float(theme.fs_title)
    if heading == 2:
        return float(theme.fs_large + 4)
    if heading == 3:
        return float(theme.fs_large)
    return float(theme.fs_body)


def block_base_format(para: Mapping[str, Any]) -> QTextCharFormat:
    """段落的基础字符格式（标题字号 / 字重）。"""
    fmt = QTextCharFormat()
    heading = para.get("heading")
    if isinstance(heading, int) and heading > 0:
        fmt.setFontPointSize(heading_size(heading))
        fmt.setFontWeight(QFont.Weight.DemiBold)
    return fmt


# ---- 行内 ----
def apply_style(fmt: QTextCharFormat, data: Mapping[str, Any]) -> None:
    """把 `Style` 数据写进字符格式。"""
    if data.get("bold"):
        fmt.setFontWeight(QFont.Weight.Bold)
    if data.get("italic"):
        fmt.setFontItalic(True)
    if data.get("underline"):
        fmt.setFontUnderline(True)
    if data.get("strike"):
        fmt.setFontStrikeOut(True)
    color = data.get("color")
    if color:
        fmt.setForeground(QColor(str(color)))
    font = data.get("font")
    if font:
        fmt.setFontFamilies([str(font)])
    size = data.get("size")
    if isinstance(size, (int, float)) and size > 0:
        fmt.setFontPointSize(float(size))


def style_from_format(fmt: QTextCharFormat) -> dict[str, Any]:
    """从字符格式还原 `Style` 数据；全默认返回空 dict。"""
    data: dict[str, Any] = {}
    if fmt.fontWeight() >= int(QFont.Weight.Bold):
        data["bold"] = True
    if fmt.fontItalic():
        data["italic"] = True
    if fmt.fontUnderline():
        data["underline"] = True
    if fmt.fontStrikeOut():
        data["strike"] = True
    if fmt.hasProperty(QTextFormat.Property.ForegroundBrush):
        data["color"] = fmt.foreground().color().name()
    families = fmt.fontFamilies()
    if families:
        data["font"] = str(families[0])
    if fmt.hasProperty(QTextFormat.Property.FontPointSize):
        data["size"] = fmt.fontPointSize()
    return data


def style_data(style: Style) -> dict[str, Any]:
    """把 `Style` 规范成可写进字符格式的数据。"""
    return style.to_data()


# ---- 嵌入占位 ----
def marker_format(kind: str, index: int) -> QTextCharFormat:
    """嵌入占位的字符格式。"""
    fmt = QTextCharFormat()
    fmt.setProperty(MARKER_KIND, kind)
    fmt.setProperty(MARKER_INDEX, int(index))
    return fmt


def marker_from_format(fmt: QTextCharFormat) -> dict[str, int] | None:
    """从字符格式还原嵌入占位；不是占位返回 None。"""
    kind = fmt.property(MARKER_KIND)
    if kind not in _MARKER_KINDS:
        return None
    return {str(kind): int(fmt.property(MARKER_INDEX) or 0)}


__all__ = [
    "LINE_ID",
    "MARKER_INDEX",
    "MARKER_KIND",
    "OBJECT_REPLACEMENT",
    "PARA_MAP",
    "apply_paragraph",
    "apply_style",
    "block_base_format",
    "heading_size",
    "marker_format",
    "marker_from_format",
    "paragraph_from_format",
    "style_data",
    "style_from_format",
]
