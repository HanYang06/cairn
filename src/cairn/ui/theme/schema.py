# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题 schema：由**注册表 + 声明**自动派生可写内容，用于校验 / 补全 / 生成模板。

主题文件两段式：

    {
      "name": "github-dark", "dark": true,
      "token": { "bg": "#0D1117", "accent": "#2F81F7" },   # 全局令牌
      "style": {                                            # 选择器 → 声明块（CSS 式）
        "widget.Button":       { "background": "token.elevated" },
        "widget.Button:hover": { "border_color": "token.accent" }
      }
    }

选择器是点分目标（`widget.<类型>[:<状态>]`），声明键是可样式属性。加组件 / 状态 / 令牌，
schema 自动跟着变。
"""

from __future__ import annotations

from dataclasses import fields

from .tokens import Theme


class ThemeSchemaError(ValueError):
    """主题路径不在 schema 内。"""


def token_paths() -> frozenset[str]:
    """全部令牌路径：``token.<字段>``。"""
    return frozenset(f"token.{field.name}" for field in fields(Theme))


def widget_paths() -> frozenset[str]:
    """全部部件样式路径（展开形态）：``widget.<类型>[.<状态>].<属性>``。"""
    from ..components import Component  # noqa: PLC0415 — 延迟导入，避免 theme ↔ components 环

    paths: set[str] = set()
    for name, cls in Component.registry().items():
        for prop in cls.STYLABLE:
            paths.add(f"widget.{name}.{prop}")
            for state in cls.STATES:
                paths.add(f"widget.{name}.{state}.{prop}")
    return frozenset(paths)


def schema_paths() -> frozenset[str]:
    """主题可写的全部点分路径（令牌 + 部件），用于 ``validate_path``。"""
    return token_paths() | widget_paths()


def validate_path(path: str) -> None:
    """校验一个点分路径是否在 schema 内；不在则抛 :class:`ThemeSchemaError`。"""
    if path not in schema_paths():
        msg = f"未知主题路径: {path}"
        raise ThemeSchemaError(msg)


def selector_paths() -> frozenset[str]:
    """全部合法选择器：``widget.<类型>`` 与 ``widget.<类型>:<状态>``。"""
    from ..components import Component  # noqa: PLC0415 — 延迟导入

    selectors: set[str] = set()
    for name, cls in Component.registry().items():
        selectors.add(f"widget.{name}")
        for state in cls.STATES:
            selectors.add(f"widget.{name}:{state}")
    return frozenset(selectors)


# 主题文件里除两段外的元键。
META_KEYS = frozenset({"$schema", "name", "dark"})
SECTIONS = ("token", "style")

SCHEMA_ID = "https://github.com/HanYang06/cairn/schema/theme.json"

_VALUE: dict[str, object] = {"type": ["string", "number", "boolean"]}


def _declarations_schema() -> dict[str, object]:
    from ..components import Component  # noqa: PLC0415 — 延迟导入

    props: set[str] = set()
    for cls in Component.registry().values():
        props.update(cls.STYLABLE)
    return {
        "type": "object",
        "properties": dict.fromkeys(sorted(props), _VALUE),
        "additionalProperties": False,
    }


def json_schema() -> dict[str, object]:
    """把当前 schema 导出成 JSON Schema（供 IDE 校验 / 补全，落 `schema/theme.json`）。"""
    tokens = {field.name: _VALUE for field in fields(Theme)}
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": SCHEMA_ID,
        "title": "Cairn 主题文件",
        "description": "两段：token（全局令牌）+ style（选择器 → 声明块）。",
        "type": "object",
        "properties": {
            "$schema": {"type": "string"},
            "name": {"type": "string"},
            "dark": {"type": "boolean"},
            "token": {"type": "object", "properties": tokens, "additionalProperties": False},
            "style": {
                "type": "object",
                "propertyNames": {"enum": sorted(selector_paths())},
                "additionalProperties": _declarations_schema(),
            },
        },
        "additionalProperties": False,
    }


__all__ = [
    "META_KEYS",
    "SCHEMA_ID",
    "SECTIONS",
    "ThemeSchemaError",
    "json_schema",
    "schema_paths",
    "selector_paths",
    "token_paths",
    "validate_path",
    "widget_paths",
]
