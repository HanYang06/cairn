# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`ui.signal` 极简信号测试。"""

from __future__ import annotations

from cairn.ui.signal import Signal


def test_emit_calls_slots_in_order() -> None:
    signal = Signal()
    seen: list[tuple[object, ...]] = []
    signal.connect(lambda *args: seen.append(args))
    signal.connect(lambda *args: seen.append(args))
    signal.emit(1, "a")
    assert seen == [(1, "a"), (1, "a")]


def test_cancel_stops_delivery() -> None:
    signal = Signal()
    seen: list[object] = []
    subscription = signal.connect(seen.append)
    signal.emit(1)
    subscription.cancel()
    signal.emit(2)
    assert seen == [1]


def test_context_manager_cancels() -> None:
    signal = Signal()
    seen: list[object] = []
    with signal.connect(seen.append):
        signal.emit(1)
    signal.emit(2)
    assert seen == [1]
