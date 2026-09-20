# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置路径 schema：把 Facet 树编译成**定向路径树**并做校验。

- 规范形式：`app.<域>.<page>.<layout>.<com>…`。
- 写配置时**可从领域起写**（省略 `app.` 与前置段）；`resolve` 做**后缀补全**。
- 补全后必须在已登记路径里，否则报错；命中多条即**歧义**报错。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .errors import UiError

if TYPE_CHECKING:
    from .node import Node


class Schema:
    """一棵已登记的配置路径树；可选记录路径对应的节点。"""

    def __init__(self, root: str = "app") -> None:
        self.root = root
        self._paths: set[str] = set()
        self._nodes: dict[str, Node] = {}

    def add(self, path: str, node: Node | None = None) -> None:
        """登记一条规范路径（可附带其节点）。"""
        self._paths.add(path)
        if node is not None:
            self._nodes[path] = node

    def node(self, path: str) -> Node | None:
        """解析路径并返回其节点（不可寻址返回 `None`）。"""
        return self._nodes.get(self.resolve(path))

    def paths(self) -> list[str]:
        """全部规范路径（有序）。"""
        return sorted(self._paths)

    def normalize(self, path: str) -> str:
        """补上根前缀（已是规范形式的原样返回）。"""
        if path == self.root or path.startswith(f"{self.root}."):
            return path
        return f"{self.root}.{path}"

    def resolve(self, path: str) -> str:
        """解析为规范路径：先按规范形式精确匹配，再按后缀补全。"""
        full = self.normalize(path)
        if full in self._paths:
            return full
        matches = sorted(p for p in self._paths if p == path or p.endswith(f".{path}"))
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise UiError(f"未找到配置路径: {path!r}")
        raise UiError(f"配置路径有歧义: {path!r} → {matches}")

    def __contains__(self, path: object) -> bool:
        return isinstance(path, str) and self.normalize(path) in self._paths

    def __len__(self) -> int:
        return len(self._paths)

    def __repr__(self) -> str:
        return f"Schema({len(self._paths)} paths)"


__all__ = ["Schema"]
