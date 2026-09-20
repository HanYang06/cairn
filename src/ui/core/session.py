# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核 · 投影缓存、类型化模型与变更源（Qt-free）。

`Session` 是 UI 与通信主干的**接入点**：消费主干上的存储事件与领域信号，
维护投影缓存 / 模型并通知观察者；主干一变，模型自动重算（单向数据流）。
本层**不 import `feature`、不碰 `Vault`**。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, cast

from core.signal import Event, Subscription

from .model import Model

if TYPE_CHECKING:
    from core.signal import Signal

type Observer = Callable[[Event], None]


class Session:
    """UI 侧的投影缓存 + 模型 + 变更源（Qt-free）。"""

    def __init__(self, signal: Signal) -> None:
        self._signal = signal
        self._observers: list[Observer] = []
        self._cache: dict[str, Any] = {}
        self._models: list[tuple[Callable[[], Iterable[Any]], Model[Any]]] = []
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

    def projection[T](self, key: str, loader: Callable[[], T]) -> T:
        """按 key 取**类型化投影**；命中即复用缓存，主干有变更则整体失效重算。"""
        if key not in self._cache:
            self._cache[key] = loader()
        return cast("T", self._cache[key])

    def model[T](self, loader: Callable[[], Iterable[T]]) -> Model[T]:
        """建一个绑定主干的类型化模型：主干一变即重算并通知。"""
        model: Model[T] = Model(loader())
        self._models.append((loader, model))
        return model

    def close(self) -> None:
        """取消主干订阅并清空观察者 / 缓存 / 模型。"""
        self._sub.cancel()
        self._observers.clear()
        self._cache.clear()
        self._models.clear()

    def _on_event(self, event: Event) -> None:
        self._cache.clear()
        for loader, model in self._models:
            model.replace(loader())
        for callback in list(self._observers):
            callback(event)


__all__ = ["Observer", "Session"]
