# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置路径 schema：把 Facet 树编译成**定向路径树**并做校验。

- 规范形式：`app.<域>.<page>.<layout>.<com>…`。
- 写配置时**可从领域起写**（省略 `app.` 与前置段）；`resolve` 做**后缀补全**。
- 补全后必须在已登记路径里，否则报错；命中多条即**歧义**报错。
"""

from __future__ import annotations

from .errors import UiError


class Schema:
    """一棵已登记的配置路径树。"""

    def __init__(self, root: str = "app") -> None:
        self.root = root
        self._paths: set[str] = set()

    def add(self, path: str) -> None:
        """登记一条规范路径。"""
        self._paths.add(path)

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
