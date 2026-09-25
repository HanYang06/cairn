# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""从声明生成 **JSON Schema**（词表那一侧）。

JSON Schema 的模板机制就是「一堆固定关键字」：``type`` / ``properties`` /
``additionalProperties`` / ``default`` / ``description`` / ``minimum`` / ``enum`` …
照模板填即可——本项目里这些都由声明自动产出，不手写。

- ``schema/<hub>/<path>/<file>.json``：**分片词表**，对应一份值文件；
- ``schema/settings.json``：**总词表**（入口，给 IDE 与分发包看）。
"""

from __future__ import annotations

from types import UnionType
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin

from .engine import SETTINGS_SCHEMA_ID

if TYPE_CHECKING:
    from core.types.cfg import CfgItem

SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"
"""用 2020-12：与 ``schema/theme.json`` 同族，编辑器支持面最广。"""

_SIMPLE: dict[type, str] = {
    bool: "boolean",
    int: "integer",
    float: "number",
    str: "string",
    list: "array",
    tuple: "array",
    dict: "object",
    type(None): "null",
}


def root_schema(grouped: dict[Any, list[CfgItem]]) -> dict[str, Any]:
    """总词表：所有 hub 的声明汇成一份 ``properties``（键即点分路径）。"""
    properties: dict[str, Any] = {}
    for declared in grouped.values():
        for item in declared:
            properties[item.key] = property_of(item)
    return {
        "$schema": SCHEMA_DRAFT,
        "$id": SETTINGS_SCHEMA_ID,
        "title": "Cairn 配置（总词表）",
        "description": "由声明自动生成，勿手改：改配置请改 config/ 下对应的值文件。",
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }


def folder_schema(declared: list[CfgItem]) -> dict[str, Any]:
    """分片词表：只含这一份值文件里的键。

    ``additionalProperties`` **故意不设 False**：引擎的投影策略是「只补缺失的键，
    已有的键一个字都不动」（见 :meth:`ConfEngine.plan`），用户自己加的键会被保留下来；
    若在这里宣布它们非法，值文件顶部的 ``$schema`` 会让 IDE 把合法文件标成错的。
    """
    return {
        "$schema": SCHEMA_DRAFT,
        "title": "Cairn 配置",
        "description": "由声明自动生成，勿手改。",
        "type": "object",
        "properties": {
            "$schema": {"type": "string"},
            **{item.key: property_of(item) for item in declared},
        },
        "additionalProperties": True,
    }


def property_of(item: CfgItem) -> dict[str, Any]:
    """一条声明的 JSON Schema 片段。"""
    schema: dict[str, Any] = {}
    typed = type_schema(item.type)
    if typed:
        schema.update(typed)
    if item.doc:
        schema["description"] = item.doc
    if item.fillable:
        schema["default"] = item.default
    schema["x-cairn-owner"] = f"{item.module}.{item.owner}"
    schema["x-cairn-fillable"] = item.fillable
    schema["x-cairn-empty-ok"] = item.empty_ok
    return schema


def type_schema(hint: Any) -> dict[str, Any]:
    """类型 → ``{"type": …}`` / ``{"anyOf": …}``；认不出就返回空（**不猜类型**）。

    认得出的只有 :data:`_SIMPLE` 里的内建类型与 ``Union``；自定义类不下 ``object``
    之类的猜测约束——词表宁可少一条，也不给错一条。
    """
    if hint is None:
        return {}
    if isinstance(hint, type) and hint in _SIMPLE:
        schema: dict[str, Any] = {"type": _SIMPLE[hint]}
        if hint in {list, tuple}:
            schema["items"] = {}
        return schema
    if isinstance(hint, UnionType) or get_origin(hint) is Union:
        branches = [type_schema(arg) for arg in get_args(hint)]
        found = [branch for branch in branches if branch]
        return {"anyOf": found} if len(found) > 1 else (found[0] if found else {})
    return {}


__all__ = ["SCHEMA_DRAFT", "folder_schema", "property_of", "root_schema", "type_schema"]
