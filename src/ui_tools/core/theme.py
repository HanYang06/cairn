# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""主题：token 封闭词表 → QSS 编译与应用。

- `token`：外观唯一真源；样式只写引用（`token.*`）。
- `styles`：CSS 式选择器 → 声明块；选择器 `widget.<kind>[:state]`，
  编译成 `QWidget[cairnClass="<kind>"][:state]`（控件由 Qt 翻译器打标）。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

_PROP_ALIASES = {
    "radius": "border-radius",
    "border_color": "border-color",
    "font_size": "font-size",
    "font_weight": "font-weight",
    "font_family": "font-family",
}
_REF_PREFIX = "token."


def _coerce(value: Any) -> str:
    """主题值只接受字符串 / 数字；``None`` / ``bool`` 会产生非法 QSS，直接报错。"""
    if value is None or isinstance(value, bool):
        raise ValueError(f"主题值非法: {value!r}")
    if isinstance(value, (str, int, float)):
        return str(value)
    raise ValueError(f"主题值必须是字符串 / 数字: {value!r}")


class Theme:
    """token + 样式规则，可编译为 QSS。"""

    def __init__(
        self,
        tokens: Mapping[str, str] | None = None,
        styles: Mapping[str, Mapping[str, str]] | None = None,
    ) -> None:
        self._tokens: dict[str, str] = {str(k): _coerce(v) for k, v in (tokens or {}).items()}
        self._styles: dict[str, dict[str, str]] = {
            str(selector): {str(k): _coerce(v) for k, v in props.items()}
            for selector, props in (styles or {}).items()
        }

    def set_token(self, key: str, value: str) -> Theme:
        """设一个 token。"""
        self._tokens[key] = _coerce(value)
        return self

    def token(self, key: str, default: str = "") -> str:
        """取 token 值。"""
        return self._tokens.get(key, default)

    def set_style(self, selector: str, props: Mapping[str, str]) -> Theme:
        """设一条样式规则。"""
        self._styles[selector] = {str(k): _coerce(v) for k, v in props.items()}
        return self

    def resolve(self, value: str) -> str:
        """展开 `token.*` 引用；悬空引用即报错，不静默落进 QSS。"""
        if value.startswith(_REF_PREFIX):
            key = value[len(_REF_PREFIX) :]
            if key not in self._tokens:
                raise KeyError(f"未知 token 引用: {value!r}")
            return self._tokens[key]
        return value

    def to_qss(self) -> str:
        """编译为 QSS 文本。"""
        blocks: list[str] = []
        for selector, props in self._styles.items():
            lines = [f"{_selector(selector)} {{"]
            for key, value in props.items():
                prop = _PROP_ALIASES.get(key, key.replace("_", "-"))
                lines.append(f"    {prop}: {self.resolve(value)};")
            lines.append("}")
            blocks.append("\n".join(lines))
        return "\n".join(blocks)

    def apply(self, app: Any) -> None:
        """整表套用到 Qt 应用（一次）。"""
        app.setStyleSheet(self.to_qss())


def _selector(selector: str) -> str:
    """`widget.button:hover` → `QWidget[cairnClass="button"]:hover`。

    支持逗号分隔的选择器组；逐段 trim 空白。
    """
    compiled: list[str] = []
    for raw_part in selector.split(","):
        part = raw_part.strip()
        if not part:
            continue
        base, _, state = part.partition(":")
        suffix = f":{state}" if state else ""
        prefix = "widget."
        if base.startswith(prefix):
            compiled.append(f'QWidget[cairnClass="{base[len(prefix) :]}"]{suffix}')
        else:
            compiled.append(part)
    return ", ".join(compiled)


def load_theme(path: Path) -> Theme:
    """从主题文件（JSON：`token` + `style` 两段）加载；其余键忽略。"""
    data: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"主题文件必须是 JSON 对象: {path}")
    tokens = data.get("token") or {}
    styles = data.get("style") or {}
    if not isinstance(tokens, dict) or not isinstance(styles, dict):
        raise TypeError(f"主题的 'token' / 'style' 必须是对象: {path}")
    return Theme(tokens, styles)


__all__ = ["Theme", "load_theme"]
