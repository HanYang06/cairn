# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""内核对象表 + 事件引擎：按作者口述的设计验证。

- 两张表在**内核**（`Core`）里，不在引擎里；
- **内核自带引擎**（与内核同生共死），建好即把两张表交给它；
- 领域对象**继承内核 → 自动注册**（父类在 `__init_subclass__` 里替子类登记）；
- 槽是**按身份索引的寄存器**：拿什么查的，就按什么返回；
- 内核是**单例**；`put` / `get` / `drop` / `call` 这些**短 API 内部代为组事件包**。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from core.core import Core, Managed
from core.signal import Outcome, Signal
from core.storage import Storage
from core.types import ObjectNotFoundError
from core.types.event import Action, Event, Intent, Slot

if TYPE_CHECKING:
    from pathlib import Path


class Probe(Managed):
    """领域对象：**继承内核即自动注册**。"""

    name = "probe"

    def __init__(self, oid: str = "", text: str = "") -> None:
        self.id = oid
        self.text = text

    def set_text(self, text: str) -> str:
        self.text = text
        return self.text

    def read(self) -> str:
        return self.text


@pytest.fixture
def core() -> Core:
    """内核自带引擎（表**不清空**：继承即注册发生在类定义期）。"""
    return Core()


# ---- 内核是单例 ----


def test_kernel_is_a_singleton() -> None:
    assert Core() is Core()
    assert Core() is Core()  # 反复构造拿到同一个


# ---- 两张表：位置与自动注册 ----


def test_subclass_of_core_registers_itself() -> None:
    """继承内核 = 自动登记（父类替子类收成），不用自己管。"""
    assert Core.type_of("probe") is Probe
    assert Core.type_of("Probe") is Probe


def test_kernel_hands_tables_to_engine(core: Core) -> None:
    """引擎拿到的是**内核的表**（引用同一份），不是自己另开一份。"""
    note = Probe("01A", "原")
    core.register(note, oid="01A", name="probe-01A")

    assert core.signal.lookup("role_id", "01A") is note
    assert core.signal._external is core._external


def test_lookup_by_three_identities(core: Core) -> None:
    """三种身份都可查：ID / 名称 / 对象。"""
    note = Probe("01A", "原")
    core.register(note, oid="01A", name="probe-01A")

    assert core.lookup("role_id", "01A") is note
    assert core.lookup("role_name", "probe-01A") is note
    assert core.lookup("role_obj", note) is note
    assert core.lookup("role_id", "不存在") is None


def test_internal_table_is_separate_from_external(core: Core) -> None:
    """表一（内核固定件）与表二（外部对象）分开。"""

    class _Fixed:
        name = "storage"

    fixed = _Fixed()
    core.mount("storage", fixed)
    assert core.lookup("role_name", "storage") is fixed
    assert core._external["role_name"].get("storage") is None


def test_unregister_removes_object(core: Core) -> None:
    note = Probe("01A", "原")
    core.register(note, oid="01A", name="probe-01A")
    core.unregister(note)
    assert core.lookup("role_id", "01A") is None
    assert core.lookup("role_obj", note) is None


# ---- 引擎：解析、指挥、落槽 ----


def test_handle_runs_actions_in_order_and_stashes(core: Core) -> None:
    note = Probe("01A", "原文")
    core.register(note, oid="01A")
    event = Event(
        intent=Intent.PUT,
        actions=[
            Action(role_id="01A", call_function="set_text", call_arges={"text": "改过的字"}),
            Action(role_obj=note, call_function="read"),
        ],
    )

    outcome = core.signal.handle(event)

    assert outcome.ok
    assert note.text == "改过的字"
    assert [step.result for step in outcome.steps] == ["改过的字", "改过的字"]
    assert [step.identity for step in outcome.steps] == ["role_id", "role_obj"]


def test_slot_returns_by_whatever_identity_was_used(core: Core) -> None:
    """**拿什么查的，就按什么返回**。"""
    note = Probe("01A", "原文")
    core.register(note, oid="01A")
    action = Action(role_id="01A", call_function="read")
    core.signal.handle(Event(intent=Intent.GET, actions=[action]))

    assert action.slot.get("role_id") == "原文"
    with pytest.raises(KeyError):
        action.slot.get("role_obj")  # 换一种身份取不到


def test_missing_target_is_reported_not_swallowed(core: Core) -> None:
    outcome = core.signal.handle(
        Event(intent=Intent.GET, actions=[Action(role_id="无此ID", call_function="read")])
    )
    assert not outcome.ok
    assert isinstance(outcome.failed[0].error, ObjectNotFoundError)


def test_missing_method_is_reported(core: Core) -> None:
    note = Probe("01A", "原")
    core.register(note, oid="01A")
    outcome = core.signal.handle(
        Event(intent=Intent.PUT, actions=[Action(role_id="01A", call_function="no_such")])
    )
    assert not outcome.ok
    assert isinstance(outcome.failed[0].error, ObjectNotFoundError)


def test_noen_event_is_not_sent(core: Core) -> None:
    note = Probe("01A", "原")
    core.register(note, oid="01A")
    outcome = core.signal.handle(
        Event(intent=Intent.NOEN, actions=[Action(role_id="01A", call_function="read")])
    )
    assert outcome.steps == []


def test_action_without_identity_fails_loud(core: Core) -> None:
    outcome = core.signal.handle(Event(intent=Intent.GET, actions=[Action(call_function="read")]))
    assert not outcome.ok


def test_engine_is_part_of_the_kernel() -> None:
    """引擎是内核自带的一部分（与内核同生共死），**不是可缺的挂件**。"""
    kernel = Core()
    assert isinstance(kernel.signal, Signal)
    assert kernel.signal._external is kernel._external


# ---- 短 API：事件包由内核代为组 ----


def test_short_api_put_get_drop(core: Core, tmp_path: Path) -> None:
    """**目标 5 行以内办完一件事**：存 / 取 / 删各一行。"""
    core.mount("storage", Storage.create(tmp_path / "vault"))
    from core.storage import Block  # noqa: PLC0415 — 就地用

    block = Block(body=b"hi")
    core.put(block)  # 一行：存
    assert core.get(Block, block.id).read() == b"hi"  # 一行：取
    core.drop(block.id)  # 一行：删
    outcome = core.send(
        Intent.GET, Action(role_name="storage", call_function="fetch", call_arges={"oid": block.id})
    )
    assert not outcome.ok  # 删掉之后再取，取不到


def test_short_api_call_returns_result(core: Core) -> None:
    note = Probe("01A", "原")
    core.register(note, oid="01A")
    assert core.call(note, "set_text", text="改") == "改"
    assert note.text == "改"


# ---- 数据结构的形状 ----


def test_event_ids_are_distinct() -> None:
    """`default_factory` 的坑：每个事件必须是**自己的** id。"""
    assert Event(intent=Intent.GET).id != Event(intent=Intent.GET).id


def test_event_requires_intent_and_actions() -> None:
    with pytest.raises(TypeError, match="intent"):
        Event(intent="PUT")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match=r"actions\[0\]"):
        Event(intent=Intent.PUT, actions=["不是动作"])  # type: ignore[list-item]


def test_identity_priority_is_id_then_object_then_name() -> None:
    note = Probe("01A")
    assert Action(role_id="01A", role_obj=note, role_name="n").identity() == ("role_id", "01A")
    assert Action(role_obj=note, role_name="n").identity() == ("role_obj", note)
    assert Action(role_name="n").identity() == ("role_name", "n")
    assert Action().identity() == ("", None)


def test_slot_refuses_non_identity_keys() -> None:
    slot = Slot()
    with pytest.raises(KeyError, match="身份"):
        slot.add("随便的名字", 1)


def test_outcome_reports_failures() -> None:
    outcome = Outcome(event=Event(intent=Intent.GET))
    assert outcome.ok
    assert outcome.failed == []
    assert isinstance(outcome.steps, list)
    assert isinstance(outcome.slot, Slot)
    assert repr(outcome)
