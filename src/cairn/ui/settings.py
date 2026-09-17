# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 设置存储：**非领域**偏好，普通 JSON 文件（不进 bucket / 块）。

点分键读写（照主题那套的直觉）：`settings.get("window.theme")` /
`settings.set("commands.shortcuts.note.new", "Ctrl+Shift+N")`。

位置：``<root>/.cairn/ui.json``（与档案同目录，纯文件，不参与内容寻址与去重）。
领域内容是块，UI 偏好是文件——两条线不混。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SETTINGS_DIR = ".cairn"
SETTINGS_NAME = "ui.json"


class SettingsStore:
    """点分键的 JSON 设置；每次写盘即时保存。"""

    def __init__(self, root: Path | str, *, name: str = SETTINGS_NAME) -> None:
        self._path = Path(root) / SETTINGS_DIR / name
        self._data: dict[str, Any] = self._load()

    @property
    def path(self) -> Path:
        """设置文件路径。"""
        return self._path

    def as_dict(self) -> dict[str, Any]:
        """全部设置的浅拷贝。"""
        return dict(self._data)

    def get(self, path: str, default: Any = None) -> Any:
        """读点分键；缺失返回默认值。"""
        node: Any = self._data
        for key in path.split("."):
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    def set(self, path: str, value: Any) -> None:
        """写点分键并落盘。"""
        keys = path.split(".")
        node = self._data
        for key in keys[:-1]:
            child = node.get(key)
            if not isinstance(child, dict):
                child = {}
                node[key] = child
            node = child
        node[keys[-1]] = value
        self._save()

    def merge(self, values: dict[str, Any]) -> None:
        """用一棵普通 dict 覆盖设置（保留其余键），并落盘。"""
        self._data = _deep_merge(self._data, values)
        self._save()

    def _load(self) -> dict[str, Any]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        current = merged.get(key)
        if isinstance(current, dict) and isinstance(value, dict):
            merged[key] = _deep_merge(current, value)
        else:
            merged[key] = value
    return merged


__all__ = ["SETTINGS_DIR", "SETTINGS_NAME", "SettingsStore"]
