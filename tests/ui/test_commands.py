# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""命令注册表测试：登记 / 派发 / 可用性 / 快捷键覆盖。"""

from __future__ import annotations

from cairn.ui.commands import Command, CommandRegistry


def test_register_and_run() -> None:
    registry = CommandRegistry()
    seen: list[int] = []
    registry.register(Command("a", "A", seen.append))
    assert registry.run("a", 1) is True
    assert seen == [1]


def test_enabled_blocks_run() -> None:
    registry = CommandRegistry()
    registry.register(Command("a", "A", lambda _ctx: None, enabled=lambda ctx: ctx > 0))
    assert registry.is_enabled("a", 0) is False
    assert registry.run("a", 0) is False
    assert registry.run("a", 1) is True


def test_unknown_command() -> None:
    registry = CommandRegistry()
    assert registry.run("nope", None) is False
    assert registry.get("nope") is None
    assert registry.shortcut("nope") == ""


def test_shortcut_override() -> None:
    registry = CommandRegistry()
    registry.register(Command("a", "A", lambda _ctx: None, shortcut="Ctrl+A"))
    assert registry.shortcut("a") == "Ctrl+A"
    registry.set_shortcuts({"a": "Ctrl+Alt+A"})
    assert registry.shortcut("a") == "Ctrl+Alt+A"


def test_decorator_and_check() -> None:
    registry = CommandRegistry()
    registry.command("a", "A", check=lambda ctx: bool(ctx.get("on")))(lambda _ctx: None)
    assert registry.get("a") is not None
    assert registry.is_checked("a", {"on": True}) is True
    assert registry.is_checked("a", {}) is False
