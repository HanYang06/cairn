# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题包加载：扫描 `config/theme/*.json`，文件名即主题名。

主题文件**两段式**（CSS 式选择器）：
    {
      "name": "github-dark", "dark": true,
      "token": { "bg": "#0D1117", "accent": "#2F81F7" },   # 全局令牌
      "style": {                                            # 选择器 → 声明块
        "widget.Button":       { "background": "token.elevated" },
        "widget.Button:hover": { "border_color": "token.accent" }
      }
    }

选择器点名目标（`widget.<类型>[:<状态>]`），声明键是属性。加载时展开为点分路径并按 schema
校验；写错段名 / 选择器 / 属性直接报错。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from .schema import META_KEYS, SECTIONS, ThemeSchemaError, validate_path
from .themes import DARK, LIGHT
from .tokens import Theme

THEME_DIR_ENV = "CAIRN_THEME_DIR"
_THEME_DIR_REL = Path("config") / "theme"
_WIDGET_PREFIX = "widget."


def repo_root() -> Path:
    """从本文件向上找含 ``pyproject.toml`` 的目录。"""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    return here.parents[3]


def theme_dir() -> Path:
    """主题目录：``CAIRN_THEME_DIR`` 覆盖，否则 ``<repo>/config/theme``。"""
    override = os.environ.get(THEME_DIR_ENV, "").strip()
    if override:
        return Path(override)
    return repo_root() / _THEME_DIR_REL


def list_themes() -> dict[str, Path]:
    """扫描主题目录：``{文件名(去扩展): 路径}``。"""
    directory = theme_dir()
    if not directory.is_dir():
        return {}
    return {path.stem: path for path in sorted(directory.glob("*.json"))}


@dataclass(frozen=True, slots=True)
class ThemeFile:
    """一个主题包：令牌主题 + 部件规则。"""

    name: str
    dark: bool
    theme: Theme
    rules: dict[str, str]
    source: Path


def load_theme(path: Path | str) -> ThemeFile:
    """读取并校验一个主题文件；未知段 / 选择器 / 属性抛 :class:`ThemeSchemaError`。"""
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = f"主题文件必须是 JSON 对象: {source}"
        raise ThemeSchemaError(msg)
    _reject_unknown_sections(data)

    overrides = _parse_tokens(data.get("token"))
    rules = _parse_style(data.get("style"))
    name = str(data.get("name") or source.stem)
    dark = bool(data.get("dark", False))
    base = DARK if dark else LIGHT
    theme = _build_theme(base, name=name, dark=dark, overrides=overrides)
    return ThemeFile(name=name, dark=dark, theme=theme, rules=rules, source=source)


def _reject_unknown_sections(data: dict[str, Any]) -> None:
    unknown = set(data) - (META_KEYS | set(SECTIONS))
    if unknown:
        msg = f"未知主题配置段: {', '.join(sorted(unknown))}"
        raise ThemeSchemaError(msg)


def _parse_tokens(block: Any) -> dict[str, Any]:
    if block is None:
        return {}
    if not isinstance(block, dict):
        msg = "token 段必须是对象"
        raise ThemeSchemaError(msg)
    overrides: dict[str, Any] = {}
    for key, value in block.items():
        validate_path(f"token.{key}")
        overrides[str(key)] = value
    return overrides


def _parse_style(block: Any) -> dict[str, str]:
    if block is None:
        return {}
    if not isinstance(block, dict):
        msg = "style 段必须是对象"
        raise ThemeSchemaError(msg)
    rules: dict[str, str] = {}
    for selector, declarations in block.items():
        if not isinstance(declarations, dict):
            msg = f"选择器 {selector} 的声明必须是对象"
            raise ThemeSchemaError(msg)
        type_name, state = _split_selector(selector)
        for prop, value in declarations.items():
            path = f"widget.{type_name}.{state}.{prop}" if state else f"widget.{type_name}.{prop}"
            validate_path(path)
            rules[path] = str(value)
    return rules


def _split_selector(selector: str) -> tuple[str, str]:
    """把 ``widget.Button:hover`` 拆成 ``("Button", "hover")``。"""
    if not selector.startswith(_WIDGET_PREFIX):
        msg = f"选择器必须以 {_WIDGET_PREFIX!r} 开头: {selector}"
        raise ThemeSchemaError(msg)
    rest = selector[len(_WIDGET_PREFIX) :]
    type_name, _, state = rest.partition(":")
    if not type_name:
        msg = f"选择器缺类型: {selector}"
        raise ThemeSchemaError(msg)
    return type_name, state


def _build_theme(base: Theme, *, name: str, dark: bool, overrides: dict[str, Any]) -> Theme:
    merged: dict[str, Any] = {field.name: getattr(base, field.name) for field in fields(Theme)}
    merged["name"] = name
    merged["dark"] = dark
    merged.update(overrides)
    return Theme(**merged)


__all__ = ["THEME_DIR_ENV", "ThemeFile", "list_themes", "load_theme", "repo_root", "theme_dir"]
