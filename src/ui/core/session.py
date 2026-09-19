# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核 · 投影缓存与变更源（Qt-free）。

`Session` 是 UI 与通信主干的**接入点**：消费主干上的存储事件与领域信号，
维护投影缓存并通知观察者。Qt 桥（后续 `bridge`）把观察者接到 Qt 信号上。

本层**不 import `feature`、不碰 `Vault`**：只持有 `Signal`，拿到的对象按契约消费。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from core.signal import Event, Subscription

if TYPE_CHECKING:
    from core.signal import Signal

type Observer = Callable[[Event], None]


class Session:
    """UI 侧的投影缓存 + 变更源（Qt-free）。"""

    def __init__(self, signal: Signal) -> None:
        self._signal = signal
        self._observers: list[Observer] = []
        self._cache: dict[str, Any] = {}
        self._sub: Subscription = signal.events.subscribe(self._on_event, Event)

    @property
    def signal(self) -> Signal:
        """所属通信主干。"""
        return self._signal

    def watch(self, callback: Observer) -> Callable[[], None]:
        """观察主干变更；返回取消函数。"""
        self._observers.append(callback)

        def cancel() -> None:
            if callback in self._observers:
                self._observers.remove(callback)

        return cancel

    def projection(self, key: str, loader: Callable[[], Any]) -> Any:
        """按 key 取投影；命中即复用缓存，主干有变更则整体失效重算。"""
        if key not in self._cache:
            self._cache[key] = loader()
        return self._cache[key]

    def close(self) -> None:
        """取消主干订阅并清空观察者 / 缓存。"""
        self._sub.cancel()
        self._observers.clear()
        self._cache.clear()

    def _on_event(self, event: Event) -> None:
        self._cache.clear()
        for callback in list(self._observers):
            callback(event)


__all__ = ["Observer", "Session"]
