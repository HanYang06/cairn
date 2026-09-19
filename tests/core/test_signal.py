# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from core.signal import Action, Domain, Signal, SignalError, Topic, action


class Counter(Domain):
    name = "Counter"
    namespace = "core"

    def __init__(self) -> None:
        self.value = 0

    @action
    def bump(self, n: int = 1) -> int:
        self.value += n
        return self.value


class Notebook(Domain):
    name = "Note"

    changed = Topic()

    def __init__(self) -> None:
        self.saved: list[int] = []

    @action
    def save(self, value: int) -> str:
        self.saved.append(value)
        self.changed.emit(value)
        return "ok"


def test_address_tree_and_unicast() -> None:
    sig = Signal()
    counter = sig.register(Counter())

    assert sig.core.Counter is counter
    assert sig.core.Counter.bump(2) == 2
    assert counter.bump(3) == 5


def test_action_handle_dispatches_through_bus() -> None:
    sig = Signal()
    counter = sig.register(Counter())
    handle = sig.core.Counter.bump

    assert isinstance(handle, Action)
    assert handle.name == "bump"
    assert handle.owner is counter
    assert handle(4) == 4


def test_action_exception_propagates() -> None:
    sig = Signal()

    class Boom(Domain):
        namespace = "core"

        @action
        def go(self) -> None:
            raise RuntimeError("boom")

    sig.register(Boom())
    with pytest.raises(RuntimeError, match="boom"):
        sig.core.Boom.go()


def test_unregistered_domain_bus_raises() -> None:
    with pytest.raises(SignalError, match="域未注册"):
        _ = Counter().bus


def test_unknown_namespace_raises() -> None:
    sig = Signal()
    with pytest.raises(SignalError, match="未知命名空间"):
        sig.register(Counter(), namespace="nope")


def test_unknown_domain_attribute_raises() -> None:
    sig = Signal()
    with pytest.raises(AttributeError, match="未注册的域"):
        _ = sig.feature.Nope


def test_topic_multicast_and_isolation() -> None:
    sig = Signal()
    note = sig.register(Notebook())
    seen: list[int] = []
    note.changed.subscribe(seen.append)

    def boom(_data: object) -> None:
        raise RuntimeError("boom")

    note.changed.subscribe(boom)
    assert note.save(1) == "ok"
    assert seen == [1]


def test_topic_subscription_cancel() -> None:
    sig = Signal()
    note = sig.register(Notebook())
    seen: list[int] = []
    sub = note.changed.subscribe(seen.append)

    note.changed.emit(1)
    sub.cancel()
    note.changed.emit(2)
    assert seen == [1]


def test_two_signals_are_isolated() -> None:
    first = Signal()
    second = Signal()
    a = first.register(Counter())
    b = second.register(Counter())

    a.bump(5)
    assert a.value == 5
    assert b.value == 0
