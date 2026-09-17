# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""工具栏里的应用级工具：**命令型 + 查询型**。

这两类不直接改笔记正文（命令型动的是笔记属性 / 视图，查询型面向文档检索），
所以元数据放 UI 层，行为由 UI 分派（命令型回调 ``Backend``；查询型为预留。
``available=False`` 表示预留位，UI 置灰、不执行。

编辑型 + 添加型的元数据在 ``domains/note/tools.py``；两者在 ``Backend.tools`` 合并成一套。
"""

from __future__ import annotations

from typing import Any

from ..domains.note.tools import ToolCategory

CATEGORY_LABELS: dict[str, str] = {
    ToolCategory.ADD: "添加",
    ToolCategory.EDIT: "编辑",
    ToolCategory.COMMAND: "命令",
    ToolCategory.QUERY: "查询",
}

COMMAND_TOOLS: list[dict[str, Any]] = [
    {
        "id": "favorite",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue734",
        "text": "",
        "label": "收藏",
        "group": "command.note",
        "available": True,
    },
    {
        "id": "archive",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue7b8",
        "text": "",
        "label": "归档",
        "group": "command.note",
        "available": True,
    },
    {
        "id": "derive",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue8f1",
        "text": "",
        "label": "复刻",
        "group": "command.note",
        "available": True,
    },
    {
        "id": "share",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue72e",
        "text": "",
        "label": "分享",
        "group": "command.note",
        "available": True,
    },
    {
        "id": "relations",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue71b",
        "text": "",
        "label": "关系",
        "group": "command.view",
        "available": True,
    },
    {
        "id": "history",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue81c",
        "text": "",
        "label": "历史",
        "group": "command.view",
        "available": True,
    },
    {
        "id": "inspector",
        "category": str(ToolCategory.COMMAND),
        "glyph": "\ue946",
        "text": "",
        "label": "属性",
        "group": "command.view",
        "available": True,
    },
]

QUERY_TOOLS: list[dict[str, Any]] = [
    {
        "id": "find",
        "category": str(ToolCategory.QUERY),
        "glyph": "\ue721",
        "text": "",
        "label": "查找",
        "group": "query.find",
        "available": False,
    },
    {
        "id": "replace",
        "category": str(ToolCategory.QUERY),
        "glyph": "\ue71c",
        "text": "",
        "label": "替换",
        "group": "query.find",
        "available": False,
    },
]

__all__ = ["CATEGORY_LABELS", "COMMAND_TOOLS", "QUERY_TOOLS"]
