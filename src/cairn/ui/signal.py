# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""极简可订阅信号（Qt-free）。

这是 UI 状态直通的最小原语：`Session` 用它广播变更，桥接层翻译成 Qt 信号。
不引入依赖追踪 / 响应式魔法，保持显式、可预测。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, Self

if TYPE_CHECKING:
    from collections.abc import Callable


class Cancellable(Protocol):
    """可取消订阅的最小协议（兼容内核事件订阅句柄）。"""

    def cancel(self) -> None:
        """退订。"""
        ...


class Subscription:
    """订阅句柄；``cancel()`` 后退订，支持 ``with``。"""

    def __init__(self, cancel: Callable[[], None]) -> None:
        self._cancel = cancel
        self._active = True

    @property
    def active(self) -> bool:
        """是否仍处于订阅状态。"""
        return self._active

    def cancel(self) -> None:
        """退订；幂等。"""
        if self._active:
            self._active = False
            self._cancel()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.cancel()


class Signal:
    """同步分发的可订阅信号；槽异常向上抛（便于暴露 bug）。"""

    def __init__(self) -> None:
        self._slots: list[Callable[..., None]] = []

    def connect(self, slot: Callable[..., None]) -> Subscription:
        """注册槽，返回可取消的订阅句柄。"""
        self._slots.append(slot)

        def _cancel() -> None:
            if slot in self._slots:
                self._slots.remove(slot)

        return Subscription(_cancel)

    def emit(self, *args: object) -> None:
        """同步调用全部槽（遍历副本，允许槽内退订）。"""
        for slot in list(self._slots):
            slot(*args)


__all__ = ["Cancellable", "Signal", "Subscription"]
