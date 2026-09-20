# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt-free 通信主干：统一调用总线 / 对象寻址空间。

设计口径见 `docs/architecture/ui-kernel.md` 与
`.agents/skills/memory/references/decisions.md`「通信主干 = 统一调用总线」。
"""

from __future__ import annotations

from .bus import Signal
from .events import (
    Event,
    EventBus,
    Handler,
    ObjectDeleted,
    ObjectPut,
    Subscription,
)
from .service import (
    Action,
    BoundTopic,
    Domain,
    SignalError,
    SignalHandler,
    Topic,
    action,
)

__all__ = [
    "Action",
    "BoundTopic",
    "Domain",
    "Event",
    "EventBus",
    "Handler",
    "ObjectDeleted",
    "ObjectPut",
    "Signal",
    "SignalError",
    "SignalHandler",
    "Subscription",
    "Topic",
    "action",
]
