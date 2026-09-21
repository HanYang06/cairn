# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""最小类型表：类型元数据（``type`` / ``role`` / ``name`` / ``fields`` / ``deps``）。

- **定义时登记**（``Block.__init_subclass__`` / ``Domain.__init_subclass__``），运行时**只读**。
- 推理一律看这里（`type` 字符串 + `role`），不做 `isinstance` 满天飞——跨边界继承链不跟随。
- `role` 两种：`domain`（域：管理型、单例、无 ID）/ `data`（存储数据结构：有 ID）。
  两者**可同名**（`Note` 与 `NoteData` 都是 `cairn.note`），故按 `(type, role)` 分键。
- 不做通用类型系统：词表封闭，够用即止。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import builtins

ROLE_DOMAIN = "domain"
ROLE_DATA = "data"


@dataclass(frozen=True)
class TypeInfo:
    """一个类型的元数据。"""

    type: str
    role: str
    cls: builtins.type
    name: str = ""
    fields: tuple[str, ...] = ()
    deps: tuple[str, ...] = ()


_TYPES: dict[tuple[str, str], TypeInfo] = {}


def register(info: TypeInfo) -> None:
    """登记（同名同角色覆盖）一个类型。"""
    _TYPES[(info.type, info.role)] = info


def type_info(type_name: str, *, role: str | None = None) -> TypeInfo | None:
    """按 `type`（可加 `role` 限定）取元数据。

    同名同时有域与数据（如 `cairn.note`）时，不指定 `role` 默认取**域**。
    """
    if role is not None:
        return _TYPES.get((type_name, role))
    return _TYPES.get((type_name, ROLE_DOMAIN)) or _TYPES.get((type_name, ROLE_DATA))


def types(role: str | None = None) -> list[TypeInfo]:
    """全部类型（可按 `role` 过滤），按 `(type, role)` 排序。"""
    items = sorted(_TYPES.values(), key=lambda info: (info.type, info.role))
    return [info for info in items if info.role == role] if role is not None else items


def collect_fields(cls: type) -> tuple[str, ...]:
    """类上声明的字段名（`Attr` / `Data` / `BodyField` 描述符）。"""
    return tuple(
        name
        for name, value in vars(cls).items()
        if not name.startswith("_") and hasattr(value, "key") and hasattr(value, "__set_name__")
    )


__all__ = [
    "ROLE_DATA",
    "ROLE_DOMAIN",
    "TypeInfo",
    "collect_fields",
    "register",
    "type_info",
    "types",
]
