# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""描述树 → 目标树：翻译器注册表 + 单向编译一次。

每个 `kind` 注册一个翻译器；编译深度优先、单向一次，不做 reconciler。
Qt 翻译器在 M1 接上，这里只给通用管线（可先注册记录型翻译器做测试）。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from .errors import UiError
from .node import Node

if TYPE_CHECKING:
    from collections.abc import Callable

type Translator = Callable[[Node, list[object]], object]
"""翻译器：把一个节点 + 已编译子件翻成目标对象。"""


class Compiler:
    """描述树编译器：按 `kind` 查翻译器，深度优先、单向一次。"""

    def __init__(self) -> None:
        self._translators: dict[str, Translator] = {}

    def register(self, kind: str, translator: Translator) -> Self:
        """登记某类型的翻译器（同名覆盖）。"""
        self._translators[kind] = translator
        return self

    def compile(self, node: Node) -> object:
        """编译一个节点及其子树；未登记翻译器即报错。"""
        children: list[object] = []
        for placed in node.children():
            child = placed.component
            children.append(self.compile(child) if isinstance(child, Node) else child)
        handler = self._translators.get(node.kind)
        if handler is None:
            raise UiError(f"未注册的翻译器: {node.kind}")
        return handler(node, children)

    def kinds(self) -> list[str]:
        """已登记翻译器的类型。"""
        return sorted(self._translators)


__all__ = ["Compiler", "Translator"]
