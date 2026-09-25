# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 内核 · 投影缓存、类型化模型与变更源（Qt-free）。

`Session` 是 UI 与内核**引擎**的接入点：订阅引擎上的事件包，维护投影缓存 / 模型并
通知观察者；链路上有事件包跑过，模型自动重算（单向数据流）。
本层**不 import `feature`、不碰 `Core`/`Storage` 内部**——只认事件流。
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, cast

from core.types.event import Event

from .model import Model

if TYPE_CHECKING:
    from core.signal import Signal, Subscription

type Observer = Callable[[Event], None]

_log = logging.getLogger(__name__)


class Session:
    """UI 侧的投影缓存 + 模型 + 变更源（Qt-free）。"""

    def __init__(self, engine: Signal) -> None:
        self._engine = engine
        self._observers: list[Observer] = []
        self._cache: dict[str, Any] = {}
        self._models: list[tuple[Callable[[], Iterable[Any]], Model[Any]]] = []
        self._closed = False
        self._sub: Subscription = engine.subscribe(self._on_event)

    @property
    def engine(self) -> Signal:
        """所属内核引擎（事件流）。"""
        return self._engine

    def watch(self, callback: Observer) -> Callable[[], None]:
        """观察主干变更；返回取消函数（重复注册去重，取消移除全部匹配）。"""
        self._require_open()
        if callback not in self._observers:
            self._observers.append(callback)

        def cancel() -> None:
            self._observers[:] = [item for item in self._observers if item != callback]

        return cancel

    def projection[T](self, key: str, loader: Callable[[], T]) -> T:
        """按 key 取**类型化投影**；命中即复用缓存，主干有变更则整体失效重算。"""
        self._require_open()
        if key not in self._cache:
            self._cache[key] = loader()
        return cast("T", self._cache[key])

    def model[T](self, loader: Callable[[], Iterable[T]]) -> Model[T]:
        """建一个绑定主干的类型化模型：主干一变即重算并通知。"""
        self._require_open()
        model: Model[T] = Model(loader())
        self._models.append((loader, model))
        return model

    def release(self, model: Model[Any]) -> None:
        """注销一个由 ``model()`` 建的模型；主干变更不再重算它。"""
        self._require_open()
        self._models = [(loader, item) for loader, item in self._models if item is not model]

    def close(self) -> None:
        """取消主干订阅并清空观察者 / 缓存 / 模型；此后入口调用即报错。"""
        if self._closed:
            return
        self._sub.cancel()
        self._observers.clear()
        self._cache.clear()
        self._models.clear()
        self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("Session 已关闭")

    def _on_event(self, event: Event) -> None:
        self._cache.clear()
        for loader, model in list(self._models):  # 迭代副本：回调可能增删模型
            try:
                model.replace(loader())
            except Exception:  # noqa: BLE001 — 单个 loader 失败不应拖垮其余模型
                _log.exception("Session 模型重算失败")
        for callback in list(self._observers):
            try:
                callback(event)
            except Exception:  # noqa: BLE001 — 单个观察者失败不应中断其余通知
                _log.exception("Session 观察者执行失败")


__all__ = ["Observer", "Session"]
