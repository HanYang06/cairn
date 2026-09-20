# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""架构红线：`ui_tools` 不依赖存储实现与领域层。"""

from __future__ import annotations

import ast
from pathlib import Path

UI_DIR = Path(__file__).resolve().parents[1] / "src" / "ui_tools"

_FORBIDDEN = ("feature", "core.storage", "core.vault")


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.append(node.module)
    return names


def test_ui_does_not_import_storage_or_feature() -> None:
    offenders: list[tuple[str, str]] = []
    for path in UI_DIR.rglob("*.py"):
        offenders.extend(
            (path.name, name)
            for name in _imports(path)
            if any(name == bad or name.startswith(f"{bad}.") for bad in _FORBIDDEN)
        )

    assert offenders == []
