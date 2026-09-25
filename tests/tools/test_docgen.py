# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`tools/docgen.py`：配置参考页与 docstring 覆盖率报告。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import docgen  # noqa: E402

SAMPLE = {
    "properties": {
        "z.last": {
            "type": "boolean",
            "default": False,
            "description": "最后一个",
            "x-cairn-owner": "core.demo.Z",
        },
        "a.first": {
            "type": "string",
            "default": "x",
            "description": "第一个",
            "x-cairn-owner": "core.demo.A",
        },
        "m.none": {"type": "integer", "description": "没有默认值", "x-cairn-owner": "core.demo.M"},
    }
}


def test_table_rows_sorted_and_complete() -> None:
    """表按点分键排序，且每个键都有一行、字段齐全。"""
    table = docgen.config_table(SAMPLE)
    lines = [line for line in table.splitlines() if line.startswith("| `")]
    assert len(lines) == 3
    assert lines[0].startswith("| `a.first`")
    assert lines[1].startswith("| `m.none`")
    assert lines[2].startswith("| `z.last`")


def test_table_renders_defaults() -> None:
    """布尔默认值渲染成 `true` / `false`；缺默认值渲染成 `—`。"""
    table = docgen.config_table(SAMPLE)
    assert "`false`" in table
    assert "| `m.none` | `integer` | — | 没有默认值 |" in table


def test_render_page_has_spdx_and_generated_banner() -> None:
    """整页自带 SPDX 头与「勿手改」声明。"""
    page = docgen.render_page(SAMPLE)
    assert page.startswith("<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->")
    assert "请勿手改" in page
    assert "全部配置项（3 条）" in page


def test_repo_page_matches_schema() -> None:
    """入库的 `docs/reference/config.md` 与词表一致（防漂移门禁的核心断言）。"""
    assert docgen.current_page() == docgen.render_page()


def test_repo_schema_is_readable() -> None:
    """总词表存在且有属性（否则生成出来的是一张空表）。"""
    settings = docgen.read_settings()
    assert settings["properties"]


def test_missing_schema_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """词表缺失时明确报错，不静默出空表。"""
    monkeypatch.setattr(docgen, "SETTINGS_SCHEMA", ROOT / "schema" / "definitely-absent.json")
    with pytest.raises(FileNotFoundError):
        docgen.read_settings()


def test_docstring_report_mentions_counts() -> None:
    """覆盖率报告给出「已写 / 总数」与缺口模块。"""
    report = docgen.coverage_report()
    documented, total, _ = docgen.docstring_stats()
    assert f"{documented}/{total}" in report
    assert 0 < documented <= total
