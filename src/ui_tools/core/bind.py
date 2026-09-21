# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""绑定登记处：UI 信号 → 领域动作 / 本类方法。

`self.bind` 是 Facet（或页面）持有的**登记处对象**，随其生命周期释放；只声明、不即时连接，
真正连接在编译 / 挂载阶段。
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import UiError
from .signal import UiSignal


@dataclass(frozen=True)
class Binding:
    """一条绑定：`source` → `target`。"""

    source: object
    target: object


class Bind:
    """绑定登记处：只声明、不即时连接；真正连接在编译 / 挂载阶段。"""

    def __init__(self) -> None:
        self._items: list[Binding] = []

    def add(self, source: object, target: object) -> Binding:
        """登记一条绑定：`source` = UI 信号，`target` = 领域动作或本类方法。"""
        binding = Binding(source=source, target=target)
        self._items.append(binding)
        return binding

    def items(self) -> list[Binding]:
        """全部绑定（按登记顺序）。"""
        return list(self._items)

    def compile(self) -> list[Binding]:
        """编译校验：源须为 UI 信号、目标须可调用；否则即报错。"""
        for binding in self._items:
            if not isinstance(binding.source, UiSignal):
                raise UiError(f"绑定源不是 UI 信号: {binding.source!r}")
            if not callable(binding.target):
                raise UiError(f"绑定目标不可调用: {binding.target!r}")
        return list(self._items)

    def clear(self) -> None:
        """清空绑定。"""
        self._items.clear()

    def __repr__(self) -> str:
        return f"Bind({len(self._items)})"


__all__ = ["Bind", "Binding"]
