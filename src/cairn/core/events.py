"""内核事件总线：类型化变更通知。

Qt-free、传输无关：桌面端适配成 Qt 信号，服务端转发到自己的通道。
事件在**提交之后**发出，监听者看到的永远是已落盘状态。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock

from .types import Oid, Space, SpaceId

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Event:
    """所有内核事件的基类。"""


@dataclass(frozen=True, slots=True)
class VaultUnlocked(Event):
    vault_id: str


@dataclass(frozen=True, slots=True)
class VaultLocked(Event):
    vault_id: str


@dataclass(frozen=True, slots=True)
class SpaceCreated(Event):
    space: Space


@dataclass(frozen=True, slots=True)
class ObjectPut(Event):
    oid: Oid
    space_id: SpaceId
    type: str
    seq: int
    created: bool


@dataclass(frozen=True, slots=True)
class ObjectDeleted(Event):
    oid: Oid


Handler = Callable[[Event], None]


@dataclass(slots=True)
class _Subscription:
    handler: Handler
    event_type: type[Event]


class Subscription:
    """订阅句柄；``cancel()`` 后不再收到事件，支持 with。"""

    def __init__(self, bus: EventBus, inner: _Subscription) -> None:
        self._bus = bus
        self._inner = inner
        self._active = True

    def cancel(self) -> None:
        if self._active:
            self._bus._remove(self._inner)
            self._active = False

    def __enter__(self) -> Subscription:
        return self

    def __exit__(self, *exc: object) -> None:
        self.cancel()


class EventBus:
    """同步分发的事件总线；处理器异常被隔离，不影响发布者。"""

    def __init__(self) -> None:
        self._subscriptions: list[_Subscription] = []
        self._lock = Lock()

    def subscribe(
        self,
        handler: Handler,
        event_type: type[Event] = Event,
    ) -> Subscription:
        inner = _Subscription(handler=handler, event_type=event_type)
        with self._lock:
            self._subscriptions.append(inner)
        return Subscription(self, inner)

    def _remove(self, inner: _Subscription) -> None:
        with self._lock:
            if inner in self._subscriptions:
                self._subscriptions.remove(inner)

    def emit(self, event: Event) -> None:
        with self._lock:
            targets = [s for s in self._subscriptions if isinstance(event, s.event_type)]
        for target in targets:
            try:
                target.handler(event)
            except Exception:
                _logger.exception("事件处理器异常: %s", type(event).__name__)


__all__ = [
    "Event",
    "EventBus",
    "Handler",
    "ObjectDeleted",
    "ObjectPut",
    "SpaceCreated",
    "Subscription",
    "VaultLocked",
    "VaultUnlocked",
]
