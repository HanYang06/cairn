# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""节点词汇表：已登记类型 + 元数据。

节点按 `kind` 自动登记（见 `Node.__init_subclass__`）；本模块对外给出查表与词汇视图，
供配置 schema、主题校验与编译使用。
"""

from __future__ import annotations

from .node import Node, registered_kinds


def kinds() -> dict[str, type[Node]]:
    """已登记的节点类型：`kind → 类`。"""
    return registered_kinds()


def vocabulary() -> dict[str, dict[str, list[str]]]:
    """词汇表：`kind → {stylable, states}`（外观 / 状态的可选词，供 schema）。"""
    return {
        kind: {"stylable": sorted(cls.STYLABLE), "states": sorted(cls.STATES)}
        for kind, cls in registered_kinds().items()
    }


__all__ = ["kinds", "vocabulary"]
