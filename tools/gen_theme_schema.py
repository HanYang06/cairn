# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""生成 `schema/theme.json`（主题文件的 JSON Schema，供 IDE 校验 / 补全）。

改动主题 schema（组件 / 状态 / 令牌）后运行：
    uv run python tools/gen_theme_schema.py
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.ui.theme import json_schema

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "schema" / "theme.json"


def main() -> int:
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(json_schema(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
