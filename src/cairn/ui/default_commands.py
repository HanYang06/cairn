# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内置命令：在这里「一处声明」，菜单 / 工具栏 / 快捷键都可从注册表派生。

命令函数接收 `App`（上下文）；行为保持在应用层，不散落到各处。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .commands import Command, CommandRegistry

if TYPE_CHECKING:
    from .root import App


def _new_note(app: App) -> None:
    app.create_note(title="新笔记")


def _save(app: App) -> None:
    app.flush_body()


def install(registry: CommandRegistry) -> None:
    """登记 Cairn 内置命令。"""
    registry.register(Command("note.new", "新建笔记", _new_note, shortcut="Ctrl+N", group="note"))
    registry.register(Command("note.save", "保存", _save, shortcut="Ctrl+S", group="note"))


__all__ = ["install"]
