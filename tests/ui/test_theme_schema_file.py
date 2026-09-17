# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`schema/theme.json` 与生成器保持一致（防漂移）。"""

from __future__ import annotations

import json

from cairn.ui.theme import json_schema, repo_root


def test_schema_file_matches_generated() -> None:
    target = repo_root() / "schema" / "theme.json"
    assert target.is_file(), "运行 uv run python tools/gen_theme_schema.py 生成 schema/theme.json"
    committed = json.loads(target.read_text(encoding="utf-8"))
    assert committed == json_schema()
