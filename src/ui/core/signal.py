# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 侧信号代理（Qt-free 占位）。

Bind 的 `source` 是 UI 侧信号；本类给出与 Qt 无关的稳定表述，编译阶段再接真实 Qt 信号。
作者只面对 `UiSignal`，不接触 `QEvent` / Qt 信号对象。
"""

from __future__ import annotations


class UiSignal:
    """一条 UI 侧信号的稳定表述（名称 + 可选参数表）。"""

    def __init__(self, name: str = "", *, args: tuple[str, ...] = ()) -> None:
        self.name = name
        self.args = tuple(args)

    def __repr__(self) -> str:
        return f"UiSignal({self.name!r})"


__all__ = ["UiSignal"]
