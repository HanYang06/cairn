# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""架构红线（按 `kernel-spec.md` §7）。

1. `ui_tools` 只认**门户**：不 import 领域（`feature`）、不碰存储实现（`core.storage`）、
   不碰 `Core` 内部；它消费的是 `core.kernel` 的事件与信号面。
2. **不允许两套同类机制并存**：内核 `core.kernel` 不得再引旧门户（已删除的 `core.signal`），
   也不得引领域。
"""

from __future__ import annotations

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
UI_DIR = SRC / "ui_tools"
KERNEL_DIR = SRC / "core" / "kernel"

_UI_FORBIDDEN = ("feature", "core.storage", "core.kernel.core", "core.kernel.storage")
_KERNEL_FORBIDDEN = ("feature", "core.signal")


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(f"{'.' * node.level}{node.module}")
    return names


def _offenders(root: Path, forbidden: tuple[str, ...]) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for path in root.rglob("*.py"):
        found.extend(
            (path.name, name)
            for name in _imports(path)
            if any(name == bad or name.startswith(f"{bad}.") for bad in forbidden)
        )
    return found


def test_ui_does_not_import_storage_or_feature() -> None:
    assert _offenders(UI_DIR, _UI_FORBIDDEN) == []


def test_kernel_does_not_import_feature_or_old_portal() -> None:
    assert _offenders(KERNEL_DIR, _KERNEL_FORBIDDEN) == []
