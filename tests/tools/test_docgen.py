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


def test_coverage_gate_flag_controls_the_exit_code() -> None:
    """报告模式不阻断；`--gate` 低于阈值即非零——是否当门禁由调用方显式选择。"""
    assert docgen.main(["--coverage"]) == 0

    expected = 1 if docgen.coverage_ratio() < docgen.DOCSTRING_MIN else 0
    assert docgen.main(["--coverage", "--gate"]) == expected


def test_unknown_argument_is_rejected() -> None:
    """未知参数必须报错退出：拼错成 `--chek` 不得静默落进默认的防漂移门禁。"""
    assert docgen.main(["--chek"]) == 1
    assert docgen.main(["--wrte"]) == 1
    assert docgen.main(["--gate"]) == 0  # `--gate` 单独出现即普通防漂移检查


def test_table_escapes_the_description_cell() -> None:
    """说明里的 `|` 与换行不得撑破表格（`doc=` 是自由文本，生成器不能假设它干净）。"""
    table = docgen.config_table(
        {"properties": {"k": {"type": "string", "description": "a|b\nc", "default": "x"}}}
    )

    assert "a\\|b<br>c" in table
    row = next(line for line in table.splitlines() if line.startswith("| `k`"))
    assert row.replace("\\|", "").count("|") == 6  # 每行仍是 5 列（转义的那个不算分隔符）


def test_public_defs_skips_function_locals(tmp_path: Path) -> None:
    """函数体内部的局部 `def` 不算公共 API：文档站不渲染它，计入只会稀释覆盖率。"""
    source = tmp_path / "sample.py"
    source.write_text(
        "def outer():\n"
        "    def inner():\n"
        "        return 1\n"
        "    return inner()\n"
        "\n"
        "class Public:\n"
        "    def method(self) -> int:\n"
        "        def nested() -> int:\n"
        "            return 2\n"
        "        return nested()\n",
        encoding="utf-8",
    )

    names = [node.name for node in docgen._public_defs(source)]

    assert names == ["outer", "Public", "method"]
