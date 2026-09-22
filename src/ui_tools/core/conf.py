# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Facet 配置：封闭词表（`theme`）＋ 开放词表（`attr`）。

键为**点分路径**，单点 `set`（覆盖）/ `add`（新增）。整体替换才用赋值，不做链式。
"""

from __future__ import annotations

from typing import Any


class ConfGroup:
    """一组配置：点分路径 + 单点赋值。"""

    def __init__(self, *, closed: bool = False) -> None:
        self._closed = closed
        self._values: dict[str, Any] = {}

    def set(self, path: str, value: Any) -> ConfGroup:
        """覆盖 / 新建一个键。"""
        self._values[path] = value
        return self

    def add(self, path: str, value: Any) -> ConfGroup:
        """新增一个键；已存在即报错（`set` 才是覆盖）。"""
        if path in self._values:
            raise KeyError(f"配置键已存在: {path!r}")
        self._values[path] = value
        return self

    def get(self, path: str, default: Any = None) -> Any:
        return self._values.get(path, default)

    def items(self) -> dict[str, Any]:
        return dict(self._values)

    def __repr__(self) -> str:
        kind = "closed" if self._closed else "open"
        return f"ConfGroup({kind}, {len(self._values)})"


class Conf:
    """Facet 配置门面：`theme`（封闭，外观令牌）/ `attr`（开放，行为属性）。"""

    def __init__(self) -> None:
        self.theme = ConfGroup(closed=True)
        self.attr = ConfGroup(closed=False)


__all__ = ["Conf", "ConfGroup"]
