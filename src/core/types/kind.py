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

from dataclasses import dataclass, replace
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import builtins

ROLE_DOMAIN = "domain"
ROLE_DATA = "data"


def type_name(value: object) -> str:
    """把类型输入归一成字符串：`Enum` 取值，其余 `str()`（枚举 / 字符串可互换）。"""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def identity_key(identity: str, value: object) -> object:
    """按身份算**查表键**：``role_obj`` 要带类型标签，ID / 名称原样。

    "拿什么查就按什么返回"的前提是**登记与查询用同一套键**——算法只此一处，
    免得内核与引擎各写一份、迟早漂移（`role_obj` 那格就踩过一次）。
    """
    if identity != "role_obj":
        return value
    try:
        hash(value)
    except TypeError:
        return (type(value), id(value))
    return (type(value), value)


def unit_names(declared: object) -> tuple[str, ...]:
    """把"声明"归一成 `type` 名元组：单个数据类，或它们的列表 / 元组。

    域服务用它把 ``data`` / ``light`` 声明转成类型名（``Block`` 子类自带 ``type``）。
    声明项取不到 ``type`` 时**抛错**：静默跳过会让 ``units`` 悄悄残缺，
    下游 ``unit_infos`` 也就不再报错，把"写错了"伪装成"本来就没有"。
    """
    if declared is None:
        return ()
    items = declared if isinstance(declared, (list, tuple)) else (declared,)
    names: list[str] = []
    for item in items:
        name = type_name(getattr(item, "type", "") or "")
        if not name:
            raise LookupError(f"声明的数据单元取不到 type：{item!r}")
        names.append(name)
    return tuple(names)


@dataclass(frozen=True)
class TypeInfo:
    """一个类型的元数据。

    `units` 只对域有意义：**最小数据单元**——一组既有数据类型的 `type`（通常一个，
    也可多个），UI 顺着这些类型拿字段即可，**不另立字段表**（避免重复维护）。
    所有单元都是 `Block` 子类，`Block` 就是那个**公共锚点**：任何单元都能顺着它往上找。
    """

    type: str
    role: str
    cls: builtins.type
    name: str = ""
    fields: tuple[str, ...] = ()
    deps: tuple[str, ...] = ()
    units: tuple[str, ...] = ()


_TYPES: dict[tuple[str, str], TypeInfo] = {}


def register(info: TypeInfo) -> None:
    """登记（同名同角色覆盖）一个类型；键与值都按值归一（枚举 / 字符串可互换）。

    归一在**登记口**一次做完：只归一键而放着值不管，会让 ``types()`` 按原始形态排序、
    让 ``domain_of`` 拿归一化后的 key 去比未归一的 ``units``——反查静默失配。
    """
    normalized = replace(
        info,
        type=type_name(info.type),
        units=tuple(type_name(unit) for unit in info.units),
        deps=tuple(type_name(dep) for dep in info.deps),
    )
    _TYPES[(normalized.type, normalized.role)] = normalized


def type_info(type_name_: object, *, role: str | None = None) -> TypeInfo | None:
    """按 `type`（可加 `role` 限定）取元数据；输入按值归一。"""
    key = type_name(type_name_)
    if role is not None:
        return _TYPES.get((key, role))
    return _TYPES.get((key, ROLE_DOMAIN)) or _TYPES.get((key, ROLE_DATA))


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


def unit_infos(domain_type: str) -> list[TypeInfo]:
    """取域的最小数据单元类型（按 `units` 解析，优先 `data` 角色）。

    单元名未登记即抛 ``LookupError``：`units` 是定义时声明，写错属于编程错误，
    静默跳过只会让下游 UI 少显示字段而无任何诊断。
    """
    domain = type_info(domain_type, role=ROLE_DOMAIN)
    if domain is None:
        return []
    result: list[TypeInfo] = []
    for name in domain.units:
        info = type_info(name, role=ROLE_DATA) or type_info(name)
        if info is None:
            raise LookupError(f"域 {domain.type!r} 声明的数据单元未登记: {name!r}")
        result.append(info)
    return result


def domain_of(unit_type: object) -> TypeInfo | None:
    """反查：某个数据类型的所属域（顺着公共锚点往上找）；输入按值归一。"""
    key = type_name(unit_type)
    for info in types(ROLE_DOMAIN):
        if key in info.units:
            return info
    return None


__all__ = [
    "ROLE_DATA",
    "ROLE_DOMAIN",
    "TypeInfo",
    "collect_fields",
    "domain_of",
    "identity_key",
    "register",
    "type_info",
    "type_name",
    "types",
    "unit_infos",
    "unit_names",
]
