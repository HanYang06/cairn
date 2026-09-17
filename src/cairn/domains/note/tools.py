# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记工具：字级（行内样式）与段级（行级属性）命令。

组织方式（基类 + 参数化实例）：

- 基类 ``Tool`` 只描述 ``id / 图标 / 文本 / 标签 / 分组``，把"作用目标"抽象成 ``ToolContext``
  （行 id + 选区 + 当前段落属性 + 行长度）。
- **行为不同**的用子类（``ToggleStyleTool`` / ``SetStyleTool`` / ``SetParagraphTool`` …）；
  **同族只差参数**的用构造参数（``ToggleStyleTool("bold")``、``AlignTool("center")``），避免参数爆炸。
- **分组与位置是数据**（``group`` 字段 + ``PRESET_LAYOUT``），不进继承链——将来用户可自行重排。

工具只服务 note（其他领域不适用）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .edit import style_at

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from .types import Note

# 字号基准（与 UI 正文一致）；``Style.size == 0`` 表示用默认。
BASE_SIZE = 13.0
MIN_SIZE = 9.0
MAX_SIZE = 48.0

DEFAULT_COLORS = ("#CF222E", "#0969DA", "#1A7F37", "#9A6700")
DEFAULT_FONTS = ("Sarasa Mono SC", "Cascadia Mono", "Consolas")


@dataclass(slots=True)
class ToolContext:
    """工具的作用目标：某行的选区 + 当前段落属性。"""

    line_id: str
    start: int = 0
    end: int = 0
    length: int = 0
    paragraph: Mapping[str, Any] = field(default_factory=dict)

    def span(self) -> tuple[int, int]:
        """作用区间：有选区用选区，否则整行。"""
        if self.end > self.start:
            return self.start, self.end
        return 0, self.length


class Tool:
    """工具基类。"""

    id: str = ""
    glyph: str = ""  # 图标字体字形（空则用 text）
    text: str = ""  # 文本字形（普通字体）
    label: str = ""
    group: str = ""

    def run(self, note: Note, ctx: ToolContext) -> None:
        """执行工具；子类实现。"""
        raise NotImplementedError

    def info(self) -> dict[str, str]:
        return {
            "id": self.id,
            "glyph": self.glyph,
            "text": self.text,
            "label": self.label,
            "group": self.group,
        }


class ToggleStyleTool(Tool):
    """切换行内布尔样式。"""

    def __init__(self, key: str, *, tid: str, text: str, label: str) -> None:
        self._key = key
        self.id = tid
        self.text = text
        self.label = label
        self.group = "font"

    def run(self, note: Note, ctx: ToolContext) -> None:
        start, end = ctx.span()
        note.toggle_style(ctx.line_id, start, end, self._key)


class SetStyleTool(Tool):
    """设置行内样式字段（颜色 / 字号 / 字体）。"""

    def __init__(
        self, patch: Mapping[str, Any], *, tid: str, glyph: str = "", text: str = "", label: str
    ) -> None:
        self._patch = dict(patch)
        self.id = tid
        self.glyph = glyph
        self.text = text
        self.label = label
        self.group = "font"

    def run(self, note: Note, ctx: ToolContext) -> None:
        start, end = ctx.span()
        note.set_style_span(ctx.line_id, start, end, self._patch)


class ColorCycleTool(Tool):
    """在预设色板里循环设置颜色，走完回到默认。"""

    id = "color"
    glyph = "\ue790"
    label = "文字颜色"
    group = "font"

    def __init__(self, palette: Sequence[str] = DEFAULT_COLORS) -> None:
        self._palette = tuple(palette)

    def run(self, note: Note, ctx: ToolContext) -> None:
        start, end = ctx.span()
        current = style_at(note.style, ctx.line_id, start).color
        if current in self._palette:
            index = self._palette.index(current) + 1
            color = self._palette[index] if index < len(self._palette) else ""
        else:
            color = self._palette[0] if self._palette else ""
        note.set_style_span(ctx.line_id, start, end, {"color": color})


class FontCycleTool(Tool):
    """在预设字体链里循环设置字体，走完回到默认。"""

    id = "font"
    text = "Aa"
    label = "字体"
    group = "font"

    def __init__(self, fonts: Sequence[str] = DEFAULT_FONTS) -> None:
        self._fonts = tuple(fonts)

    def run(self, note: Note, ctx: ToolContext) -> None:
        start, end = ctx.span()
        current = style_at(note.style, ctx.line_id, start).font
        if current in self._fonts:
            index = self._fonts.index(current) + 1
            font = self._fonts[index] if index < len(self._fonts) else ""
        else:
            font = self._fonts[0] if self._fonts else ""
        note.set_style_span(ctx.line_id, start, end, {"font": font})


class SizeTool(Tool):
    """相对调整字号。"""

    group = "font"

    def __init__(self, delta: float, *, tid: str, text: str, label: str) -> None:
        self._delta = delta
        self.id = tid
        self.text = text
        self.label = label

    def run(self, note: Note, ctx: ToolContext) -> None:
        start, end = ctx.span()
        current = style_at(note.style, ctx.line_id, start).size or BASE_SIZE
        size = max(MIN_SIZE, min(MAX_SIZE, current + self._delta))
        note.set_style_span(
            ctx.line_id, start, end, {"size": 0.0 if abs(size - BASE_SIZE) < 0.01 else size}
        )


class ClearFormatTool(Tool):
    """清掉选区（或整行）的行内样式。"""

    id = "clear-format"
    glyph = "\ue894"
    label = "清除格式"
    group = "font.clear"

    def run(self, note: Note, ctx: ToolContext) -> None:
        start, end = ctx.span()
        note.clear_style_span(ctx.line_id, start, end)


class SetParagraphTool(Tool):
    """设置行级（段落）属性；``toggle`` 为真且已生效时反向清除。"""

    def __init__(  # noqa: PLR0913 — 工具描述字段均有默认值
        self,
        patch: Mapping[str, Any],
        *,
        tid: str,
        glyph: str = "",
        text: str = "",
        label: str,
        group: str = "para",
        toggle: bool = False,
    ) -> None:
        self._patch = dict(patch)
        self._toggle = toggle
        self.id = tid
        self.glyph = glyph
        self.text = text
        self.label = label
        self.group = group

    def run(self, note: Note, ctx: ToolContext) -> None:
        if self._toggle and all(ctx.paragraph.get(k) == v for k, v in self._patch.items()):
            note.set_paragraph(ctx.line_id, dict.fromkeys(self._patch))
        else:
            note.set_paragraph(ctx.line_id, self._patch)


class IndentTool(Tool):
    """增减缩进层级。"""

    group = "para.indent"

    def __init__(self, delta: int, *, tid: str, glyph: str, label: str) -> None:
        self._delta = delta
        self.id = tid
        self.glyph = glyph
        self.label = label

    def run(self, note: Note, ctx: ToolContext) -> None:
        level = int(ctx.paragraph.get("level") or 0) + self._delta
        level = max(0, min(level, 8))
        note.set_paragraph(ctx.line_id, {"level": level or None})


class ClearParagraphTool(Tool):
    """清掉整行的段落属性。"""

    id = "clear-para"
    glyph = "\ue894"
    label = "清除段落格式"
    group = "para.clear"

    def run(self, note: Note, ctx: ToolContext) -> None:
        note.clear_paragraph(ctx.line_id)


def _registry(*tools: Tool) -> dict[str, Tool]:
    out: dict[str, Tool] = {}
    for tool in tools:
        out[tool.id] = tool
    return out


TOOLS: dict[str, Tool] = _registry(
    # ---- 字级 ----
    ToggleStyleTool("bold", tid="bold", text="B", label="加粗"),
    ToggleStyleTool("italic", tid="italic", text="I", label="斜体"),
    ToggleStyleTool("underline", tid="underline", text="U", label="下划线"),
    ToggleStyleTool("strike", tid="strike", text="S", label="删除线"),
    ColorCycleTool(),
    SizeTool(1.0, tid="size-up", text="A+", label="增大字号"),
    SizeTool(-1.0, tid="size-down", text="A-", label="减小字号"),
    FontCycleTool(),
    ClearFormatTool(),
    # ---- 段级 ----
    SetParagraphTool(
        {"align": "left"},
        tid="align-left",
        glyph="\ue8e4",
        label="左对齐",
        group="para.align",
        toggle=True,
    ),
    SetParagraphTool(
        {"align": "center"},
        tid="align-center",
        glyph="\ue8e3",
        label="居中",
        group="para.align",
        toggle=True,
    ),
    SetParagraphTool(
        {"align": "right"},
        tid="align-right",
        glyph="\ue8e2",
        label="右对齐",
        group="para.align",
        toggle=True,
    ),
    SetParagraphTool(
        {"heading": 1}, tid="h1", text="H1", label="标题 1", group="para.heading", toggle=True
    ),
    SetParagraphTool(
        {"heading": 2}, tid="h2", text="H2", label="标题 2", group="para.heading", toggle=True
    ),
    SetParagraphTool(
        {"heading": 3}, tid="h3", text="H3", label="标题 3", group="para.heading", toggle=True
    ),
    SetParagraphTool(
        {"heading": None}, tid="body", text="P", label="正文", group="para.heading", toggle=True
    ),
    SetParagraphTool(
        {"list": "bullet"},
        tid="bullet",
        glyph="\ue8fd",
        label="无序列表",
        group="para.list",
        toggle=True,
    ),
    SetParagraphTool(
        {"list": "ordered"},
        tid="ordered",
        glyph="\ue8ef",
        label="有序列表",
        group="para.list",
        toggle=True,
    ),
    IndentTool(-1, tid="indent-out", glyph="\ue8a7", label="减少缩进"),
    IndentTool(1, tid="indent-in", glyph="\ue8a9", label="增加缩进"),
    SetParagraphTool(
        {"block": "quote"},
        tid="quote",
        glyph="\ue8ac",
        label="引用",
        group="para.block",
        toggle=True,
    ),
    SetParagraphTool(
        {"block": "code"},
        tid="code",
        glyph="\ue943",
        label="代码块",
        group="para.block",
        toggle=True,
    ),
    ClearParagraphTool(),
)

# 预设布局：行 → 组 → 工具 id（用户自定义前先给这套）。
PRESET_LAYOUT: list[list[list[str]]] = [
    [
        ["bold", "italic", "underline", "strike"],
        ["color"],
        ["size-down", "size-up"],
        ["font"],
        ["clear-format"],
    ],
    [
        ["align-left", "align-center", "align-right"],
        ["h1", "h2", "h3", "body"],
        ["bullet", "ordered"],
        ["indent-out", "indent-in"],
        ["quote", "code"],
        ["clear-para"],
    ],
]


def tool_info() -> list[dict[str, str]]:
    """全部工具的元数据（供 UI 渲染）。"""
    return [tool.info() for tool in TOOLS.values()]


def run_tool(tool_id: str, note: Note, ctx: ToolContext) -> bool:
    """执行工具；未知 id 返回 ``False``。"""
    tool = TOOLS.get(tool_id)
    if tool is None:
        return False
    tool.run(note, ctx)
    return True


__all__ = [
    "BASE_SIZE",
    "DEFAULT_COLORS",
    "DEFAULT_FONTS",
    "MAX_SIZE",
    "MIN_SIZE",
    "PRESET_LAYOUT",
    "TOOLS",
    "ClearFormatTool",
    "ClearParagraphTool",
    "ColorCycleTool",
    "FontCycleTool",
    "IndentTool",
    "SetParagraphTool",
    "SetStyleTool",
    "SizeTool",
    "ToggleStyleTool",
    "Tool",
    "ToolContext",
    "run_tool",
    "tool_info",
]
