# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核事件总线：类型化变更通知。

Qt-free、传输无关：桌面端适配成 Qt 信号，服务端转发到自己的通道。
事件在**提交之后**发出，监听者看到的永远是已落盘状态。
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from threading import Lock
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ..types import Oid

_logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Event:
    """所有内核事件的基类。"""


@dataclass(frozen=True, slots=True)
class ObjectPut(Event):
    """对象已写入。``checksum`` 让监听者据此判断内容是否真的变了。"""

    oid: Oid
    type: str
    seq: int
    created: bool
    checksum: str = ""


@dataclass(frozen=True, slots=True)
class ObjectDeleted(Event):
    """对象已删除。"""

    oid: Oid


Handler = Callable[[Event], None]


@dataclass(slots=True, eq=False)
class _Subscription:
    """订阅条目；``eq=False`` 让它**按身份**匹配。

    自动生成的 ``__eq__`` 会让两条订阅互为等价（同 handler 同事件类型），
    于是 ``_remove`` 的 ``in`` / ``remove`` 可能删掉**别人**的条目——订阅两次、
    只取消其一时就出错。条目是私有实现细节，身份语义才是对的。
    """

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
            self._bus._remove(self._inner)  # noqa: SLF001 — 订阅句柄与总线同模块强耦合
            self._active = False

    def __enter__(self) -> Self:
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
    "Subscription",
]
