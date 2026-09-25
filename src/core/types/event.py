# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""事件数据结构：`Event` 数据包 + `Action` 动作结构 + `Slot` 结果寄存器。

设计出处（作者口述，2026-09-22）：

- **事件本身是单一化的**：`Event.intent` 是**单值**，回答"这个事件是什么意思、发不发"。
- **`actions` 是执行链**：它完整描述「**动作 + 目标 + 方法 + 参数**」，按 1、2、3… 顺序执行。
- **槽 = 寄存器**：动作的执行结果落进 `Slot`；**拿什么查的，就按什么返回**
  （用 ID 查的按 ID 取，用对象查的按对象取）——故它是**按身份索引的寄存器**，不是"名字→值"的表。
- **期望不用写**：调用某个方法本身就是期望的表现；有结果就有结果，没有就没有。
  判据在引擎侧：查**实际结果**是否满足（具体比较口径待作者定）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

# 槽按身份索引：三样身份各自入槽（与 Action 的三个 role_* 字段一一对应）。
_IDENTITY_KEYS = ("role_id", "role_name", "role_obj")


class Intent(Enum):
    """**事件本身的意图**（单一值）：这个事件是什么意思、发不发。

    命名说明：作者原稿叫 ``TypeAction``，与结构体 `Action` 只差前缀、极易读混，
    此处按"意图 vs 动作"分家改名；**要改回原名说一声即可**。
    """

    NOEN = "NOEN"  # 原稿拼作 NOEN（疑为 NONE）；改名会动数据，待作者定
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DEL = "DEL"


class Slot:
    """**结果寄存器**：按身份索引存取动作的执行结果。

    「拿什么查的，就按什么返回」：用 ``role_id`` 查的，结果就按 ``role_id`` 落在槽里，
    取的时候也用 ``role_id`` 取——不允许换一种身份去取（那才会"不合理"）。
    """

    def __init__(self, **identity: Any) -> None:
        self._cells: dict[str, Any] = {}
        for key, value in identity.items():
            if value:
                self._cells[key] = value

    # ---- 写 ----
    def add(self, key: str, value: Any) -> Slot:
        """登记一个身份 → 值（唯一的写入口：动作的执行结果就落在这里）。"""
        self._require_key(key)
        self._cells[key] = value
        return self

    # ---- 读 ----
    def get[T](self, key: str, cls: type[T] | None = None) -> T | Any:
        """按身份取值；取了不存在的格子即抛错（找不到就是找不到）。"""
        if key not in self._cells:
            raise KeyError(f"槽里没有这个身份：{key}")
        value = self._cells[key]
        if cls is not None and not isinstance(value, cls):
            raise TypeError(f"槽里的 {key} 不是 {cls.__name__}：{type(value).__name__}")
        return value

    def find(self, key: str) -> Any:
        """按身份取值；没登记返回 ``None``（不抛）。"""
        return self._cells.get(key)

    def holds(self, key: str) -> bool:
        """这个身份在槽里是否有值。"""
        return key in self._cells

    def keys(self) -> tuple[str, ...]:
        """槽里已登记的身份格。"""
        return tuple(self._cells)

    def clear(self) -> None:
        """清空（一次执行结束 / 重跑前）。"""
        self._cells.clear()

    def _require_key(self, key: str) -> None:
        if key not in _IDENTITY_KEYS:
            raise KeyError(f"槽只按身份索引，不认识：{key}（可用：{', '.join(_IDENTITY_KEYS)}）")

    def __repr__(self) -> str:
        return f"Slot({', '.join(self._cells) or '空'})"


@dataclass
class Action:
    """**动作结构体**：完整描述「动作 + 目标 + 方法 + 参数」。

    一个 ``Action`` 就是执行链上的一步；它的结果落进自己的 ``slot`` 寄存器。
    """

    action_type: Intent = Intent.NOEN
    role_id: str = ""
    role_name: str = ""
    role_obj: object | None = None
    call_function: str = ""
    call_args: dict[str, Any] = field(default_factory=dict)
    slot: Slot = field(default_factory=Slot)

    def identity(self) -> tuple[str, Any]:
        """这一步**拿什么查目标**：返回 ``(身份名, 身份值)``，优先 ID、其次对象、最后名称。

        作者口述：通常拿 ID 或对象查，拿名称查最少（要遍历）。
        """
        if self.role_id:
            return ("role_id", self.role_id)
        if self.role_obj is not None:
            return ("role_obj", self.role_obj)
        if self.role_name:
            return ("role_name", self.role_name)
        return ("", None)

    def __repr__(self) -> str:
        kind, value = self.identity()
        return f"Action({self.action_type.name}:{kind}={value!r}->{self.call_function})"


@dataclass
class Event:
    """**事件数据包**。

    - ``intent``：事件本身的意图（单值）——它是什么意思、发不发；
    - ``actions``：执行链（结构体列表）——具体怎么干；
    - ``source`` / ``target``：谁发的 / 目标是谁（各自独立，不再一个字段兼职两种含义）。
    """

    intent: Intent = Intent.NOEN
    actions: list[Action] = field(default_factory=list)
    source: object | str = ""
    target: object | str = ""
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.intent, Intent):
            raise TypeError(f"intent 必须是 Intent，得到 {type(self.intent).__name__}")
        for index, action in enumerate(self.actions):
            if not isinstance(action, Action):
                raise TypeError(f"actions[{index}] 必须是 Action，得到 {type(action).__name__}")

    def is_sendable(self) -> bool:
        """**发不发**：意图不是"无"才发得出去。"""
        return self.intent is not Intent.NOEN

    def __repr__(self) -> str:
        return f"Event({self.intent.name}, {len(self.actions)} 步, id={str(self.id)[:8]})"


__all__ = ["Action", "Event", "Intent", "Slot"]
