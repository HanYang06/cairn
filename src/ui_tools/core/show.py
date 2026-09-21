# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Show`：最小数据单元 → 可显示的 UI 素材（中立投影，Qt-free）。

一条**确定性**管线，输入是数据对象（一个或多个），输出合并后的素材：

- **L0 归集**：attrs 合并、ids 全并、body 收集。
- **L1 分组**：属性按来源数据类型分组（`groups`）。
- **L2 类型驱动**：按字段值类型给默认呈现（`text` / `toggle` / `chips` / `kv` / `number`）。
- **L3 body 感知**：有 body 就按 body 形态给默认呈现（`lines` / `canvas` / `media` / `raw`）。

**L4（语义推断）不做**——不假装智能。`Show` 由组织器（Facet）内部使用，开发者一般不用碰。
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

from core.types import TypeInfo, type_info, type_name

_FIELD_KINDS: tuple[tuple[type, str], ...] = (
    (bool, "toggle"),
    (str, "text"),
    (list, "chips"),
    (dict, "kv"),
    (int, "number"),
    (float, "number"),
)


def _one(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _attr_of(item: object, name: str) -> Any:
    attrs = getattr(item, "attrs", None)
    if isinstance(attrs, Mapping) and name in attrs:
        return attrs[name]
    return getattr(item, name, None)


def _ids_of(item: object, body: Any) -> list[str]:
    found: list[str] = []
    for name in ("id", "oid", "gid"):
        value = getattr(item, name, None)
        if value:
            found.append(str(value))
    lines = getattr(body, "text", None)
    if isinstance(lines, Iterable) and not isinstance(lines, (str, bytes)):
        found.extend(
            str(line["id"]) for line in lines if isinstance(line, Mapping) and "id" in line
        )
    return found


def field_kind(value: Any) -> str:
    """字段值的默认呈现（确定性映射）。"""
    for kind_type, kind in _FIELD_KINDS:
        if isinstance(value, kind_type):
            return kind
    return "text"


def body_kind(body: Any) -> str:
    """Body 的默认呈现（确定性映射）。"""
    if body is None:
        return ""
    if hasattr(body, "graphics"):
        return "canvas"
    if isinstance(body, (bytes, bytearray)):
        return "media"
    if hasattr(body, "text"):
        return "lines"
    return "raw"


@dataclass
class ShowPart:
    """一个来源数据单元在 `Show` 里的那部分。"""

    type: str
    info: TypeInfo | None
    attrs: dict[str, Any]
    ids: list[str]
    body: Any = None

    @property
    def fields(self) -> dict[str, str]:
        """本单元字段 → 默认呈现。"""
        return {name: field_kind(value) for name, value in self.attrs.items()}


@dataclass
class Show:
    """最小数据单元（可多个）→ 显示素材。"""

    parts: list[ShowPart] = field(default_factory=list)
    attrs: dict[str, Any] = field(default_factory=dict)
    groups: dict[str, list[str]] = field(default_factory=dict)
    ids: list[str] = field(default_factory=list)
    bodies: list[Any] = field(default_factory=list)

    def __init__(self, items: Any = None) -> None:
        self.parts = [self._part(item) for item in _one(items)]
        self.attrs = {}
        self.groups = {}
        self.ids = []
        self.bodies = []
        for part in self.parts:
            self.attrs.update(part.attrs)  # L0：同名后写覆盖
            self.groups.setdefault(part.type, []).extend(part.attrs)  # L1：按来源类型分组
            self.ids.extend(part.ids)
            if part.body is not None:
                self.bodies.append(part.body)

    @staticmethod
    def _part(item: object) -> ShowPart:
        type_ = type_name(getattr(item, "type", None) or type(item))
        info = type_info(type_)
        body = getattr(item, "body", None)
        names = info.fields if info is not None else ()
        attrs = {name: _attr_of(item, name) for name in names}
        if not names:
            attrs = dict(getattr(item, "attrs", None) or {})
        return ShowPart(
            type=type_,
            info=info,
            attrs=attrs,
            ids=_ids_of(item, body),
            body=body,
        )

    @property
    def title(self) -> str:
        """默认标题：`title` / `name`，否则类型名。"""
        for key in ("title", "name"):
            value = self.attrs.get(key)
            if value:
                return str(value)
        return self.parts[0].type if self.parts else ""

    @property
    def body_kinds(self) -> list[str]:
        """各 body 的默认呈现（L3）。"""
        return [kind for kind in (body_kind(body) for body in self.bodies) if kind]


__all__ = ["Show", "ShowPart", "body_kind", "field_kind"]
