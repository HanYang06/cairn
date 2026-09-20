# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""通信主干：事件 / 多播投递 + 域对象树。

- `Signal` 是总线本体：`events` 投递器、`emit` / `subscribe` 多播、`invoke` 单播。
- `core` / `feature` 是由组合根**静态挂载**的域容器（普通赋值，无注册 / 无 `__getattr__`）。

域数量少且确定，故不提供运行时注册 / 内省；插件化（契约推导）留待未来。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .events import Event, EventBus, Subscription

if TYPE_CHECKING:
    from .service import Action, BoundTopic, SignalHandler


@dataclass(frozen=True, slots=True)
class _TopicEvent(Event):
    """多播信号在底层事件总线上的载体。"""

    topic: object
    data: Any = None


class Signal:
    """进程内通信主干：事件 / 多播投递 + 单播派发。

    `core` / `feature` 由组合根赋值为域容器实例（静态声明，IDE 可识别）。
    """

    def __init__(self) -> None:
        self._events = EventBus()
        self.core: object | None = None
        self.feature: object | None = None

    @property
    def events(self) -> EventBus:
        """底层事件总线（块级事实通知）。"""
        return self._events

    def invoke(self, action: Action, *args: Any, **kwargs: Any) -> Any:
        """单播：执行动作，异常原样透传。"""
        return action._func(action._owner, *args, **kwargs)  # noqa: SLF001 — 动作句柄与总线同包强耦合

    def emit(self, topic: BoundTopic, data: Any = None) -> None:
        """多播：发出信号（订阅者异常被隔离）。"""
        self._events.emit(_TopicEvent(topic=topic, data=data))

    def subscribe(self, topic: BoundTopic, handler: SignalHandler) -> Subscription:
        """多播：按信号订阅。"""
        target = topic

        def dispatch(event: Event) -> None:
            if isinstance(event, _TopicEvent) and event.topic is target:
                handler(event.data)

        return self._events.subscribe(dispatch, _TopicEvent)

    def __repr__(self) -> str:
        return f"Signal(core={self.core is not None}, feature={self.feature is not None})"


__all__ = ["Signal"]
