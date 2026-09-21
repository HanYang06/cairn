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


class Theme:
    """token + 样式规则，可编译为 QSS。"""

    def __init__(
        self,
        tokens: Mapping[str, str] | None = None,
        styles: Mapping[str, Mapping[str, str]] | None = None,
    ) -> None:
        self._tokens: dict[str, str] = {str(k): str(v) for k, v in (tokens or {}).items()}
        self._styles: dict[str, dict[str, str]] = {
            str(selector): {str(k): str(v) for k, v in props.items()}
            for selector, props in (styles or {}).items()
        }

    def set_token(self, key: str, value: str) -> Theme:
        """设一个 token。"""
        self._tokens[key] = value
        return self

    def token(self, key: str, default: str = "") -> str:
        """取 token 值。"""
        return self._tokens.get(key, default)

    def set_style(self, selector: str, props: Mapping[str, str]) -> Theme:
        """设一条样式规则。"""
        self._styles[selector] = {str(k): str(v) for k, v in props.items()}
        return self

    def resolve(self, value: str) -> str:
        """展开 `token.*` 引用。"""
        if value.startswith(_REF_PREFIX):
            return self.token(value[len(_REF_PREFIX) :], value)
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
    """`widget.button:hover` → `QWidget[cairnClass="button"]:hover`。"""
    base, _, state = selector.partition(":")
    suffix = f":{state}" if state else ""
    prefix = "widget."
    if base.startswith(prefix):
        return f'QWidget[cairnClass="{base[len(prefix) :]}"]{suffix}'
    return selector


def load_theme(path: Path) -> Theme:
    """从主题文件（JSON：`token` + `style` 两段）加载；其余键忽略。"""
    data: dict[str, Any] = json.loads(Path(path).read_text(encoding="utf-8"))
    tokens = data.get("token") or {}
    styles = data.get("style") or {}
    return Theme(tokens, styles)


__all__ = ["Theme", "load_theme"]
