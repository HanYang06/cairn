# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置加载：把配置数据按 schema 校验后写进各节点的 `Conf`。

数据形如 `{路径: {项: 值}}`；路径可**从领域起写**，由 `Schema.resolve` 补全校验；
写不进的路径（未登记 / 歧义 / 不可寻址）一律报错，不静默失效。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .errors import UiError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .schema import Schema

_GROUPS = ("attr", "theme")


def apply_config(
    schema: Schema,
    data: Mapping[str, Mapping[str, Any]],
    *,
    group: str = "attr",
) -> None:
    """把 `data` 写进 `group`（`attr` / `theme`）配置组。"""
    if group not in _GROUPS:
        raise UiError(f"未知配置组: {group!r}（应为 {' / '.join(_GROUPS)}）")
    for path, items in data.items():
        full = schema.resolve(path)
        node = schema.node(full)
        if node is None:
            raise UiError(f"配置路径不可寻址: {path!r}")
        target = node.conf.theme if group == "theme" else node.conf.attr
        for item, value in items.items():
            target.set(item, value)


__all__ = ["apply_config"]
