# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""命令注册表：命令在代码里声明（内存），用户配置（快捷键等）另存文件。

设计取舍：
- **命令定义不持久化**——它是程序的一部分，随版本走；持久化会与代码脱节。
- **可持久化的是命令配置**：快捷键覆盖、工具栏/菜单位置与可见性，由 `settings` 存普通文件。

一处声明，菜单 / 工具栏 / 快捷键都能从注册表派生。见 `rules/references/ui-boundary.md`。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


@dataclass(frozen=True, slots=True)
class Command:
    """一条命令：身份 / 标题 / 行为，外加可选的快捷键、分组与状态判定。"""

    id: str
    title: str
    run: Callable[[Any], None]
    shortcut: str = ""
    group: str = ""
    enabled: Callable[[Any], bool] | None = None
    check: Callable[[Any], bool] | None = None


class CommandRegistry:
    """命令注册与派发；快捷键可被设置覆盖。"""

    def __init__(self) -> None:
        self._commands: dict[str, Command] = {}
        self._shortcuts: dict[str, str] = {}

    def register(self, command: Command) -> Command:
        """登记一条命令（同 id 覆盖）。"""
        self._commands[command.id] = command
        return command

    def command(  # noqa: PLR0913 — 命令声明的参数面：id/标题/快捷键/分组/可用/勾选
        self,
        command_id: str,
        title: str,
        *,
        shortcut: str = "",
        group: str = "",
        enabled: Callable[[Any], bool] | None = None,
        check: Callable[[Any], bool] | None = None,
    ) -> Callable[[Callable[[Any], None]], Command]:
        """装饰器：把函数登记成命令。"""

        def decorate(func: Callable[[Any], None]) -> Command:
            return self.register(
                Command(
                    id=command_id,
                    title=title,
                    run=func,
                    shortcut=shortcut,
                    group=group,
                    enabled=enabled,
                    check=check,
                )
            )

        return decorate

    def get(self, command_id: str) -> Command | None:
        """按 id 取命令。"""
        return self._commands.get(command_id)

    def all(self) -> list[Command]:
        """全部命令（登记顺序）。"""
        return list(self._commands.values())

    def is_enabled(self, command_id: str, ctx: Any) -> bool:
        """命令是否可用（无判定即恒可用；未登记即不可用）。"""
        command = self._commands.get(command_id)
        if command is None:
            return False
        return True if command.enabled is None else bool(command.enabled(ctx))

    def is_checked(self, command_id: str, ctx: Any) -> bool:
        """命令的开关态（用于勾选显示）。"""
        command = self._commands.get(command_id)
        if command is None or command.check is None:
            return False
        return bool(command.check(ctx))

    def set_shortcuts(self, overrides: Mapping[str, str]) -> None:
        """载入快捷键覆盖（来自设置文件）。"""
        self._shortcuts = {str(key): str(value) for key, value in overrides.items()}

    def shortcut(self, command_id: str) -> str:
        """命令生效的快捷键：设置覆盖优先，否则命令默认。"""
        override = self._shortcuts.get(command_id)
        if override:
            return override
        command = self._commands.get(command_id)
        return command.shortcut if command is not None else ""

    def run(self, command_id: str, ctx: Any) -> bool:
        """执行命令；不可用 / 未登记返回 False。"""
        command = self._commands.get(command_id)
        if command is None or not self.is_enabled(command_id, ctx):
            return False
        command.run(ctx)
        return True


__all__ = ["Command", "CommandRegistry"]
