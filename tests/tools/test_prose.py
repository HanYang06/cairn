# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`tools/prose.py`：书面语词典与检查器。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import prose  # noqa: E402


def _hits_for(text: str, filename: str = "sample.md") -> list[prose.Hit]:
    """把一段文本当 `.md` 扫一遍，返回命中。"""
    path = ROOT / filename
    assert not path.exists(), f"测试不得依赖真实文件：{filename}"
    return _scan(text)


def _scan(text: str) -> list[prose.Hit]:
    """直接走词典匹配，避免落盘。"""
    hits: list[prose.Hit] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        hits.extend(
            prose.Hit(path="<mem>", line=line_no, text=line, term=t.pattern.pattern, why=t.why)
            for t in prose._LEXICON
            if t.pattern.search(line)
        )
    return hits


@pytest.mark.parametrize(
    "text",
    [
        "这一步你必须先跑 uv sync。",
        "咱们先看配置。",
        "说白了，这就是个缓存。",
        "顺手把文档也改了。",
        "这里有个踩坑点。",
        "别手抄 SPDX 头。",
        "别慌，这不影响。",
        "文档会撒谎。",
        "这个比喻把读者吃掉了。",
        "重要!!!",
        "配置搞定。",
        "回头再补测试。",
        "反正是临时的。",
    ],
)
def test_colloquial_text_is_flagged(text: str) -> None:
    """口语样本必须被命中。"""
    assert _scan(text), f"未命中口语：{text}"


@pytest.mark.parametrize(
    "text",
    [
        "本仓库不引入 GPL 依赖。",
        "使用者须先执行 uv sync。",
        "配置声明即事实，两个投影落盘。",
        "该字段为必填项，缺失即报错。",
        "内核是单例，域服务只需创建一次。",
        "存储层必须 Qt-free、传输无关。",
        "此项已废弃，以代码为准。",
        "格式版本号不进配置，留在实现处。",
        "此处保留默认值 30 天。",
        "字段 `title` 为可选项。",
        "文档与代码不一致时应回写文档。",
        "该实现尚未落地，标注为草案。",
    ],
)
def test_written_chinese_is_not_flagged(text: str) -> None:
    """规范书面语不得误报。"""
    assert not _scan(text), f"误报：{text} -> {_scan(text)!r}"


def test_lexicon_has_no_duplicate_patterns() -> None:
    """词典内不得有重复规则。"""
    patterns = [term.pattern.pattern for term in prose._LEXICON]
    assert len(patterns) == len(set(patterns))


def test_skip_dirs_exclude_generated_output() -> None:
    """生成物与本地数据不在扫描范围。"""
    for skipped in ("site", "build", ".venv", "vault"):
        assert skipped in prose._SKIP_DIRS


def test_repo_markdown_is_clean_of_lexicon() -> None:
    """入库的手写 Markdown 不得命中词典（这是本任务的验收条件）。

    `_targets()` 返回 `(待检文件, 跳过的路径)` 二元组；本用例只要前者。
    """
    targets, _skipped = prose._targets([])
    markdown = [path for path in targets if path.suffix == ".md"]
    assert markdown, "未扫到任何 Markdown，扫描范围配置有误"
    offenders = {path.relative_to(ROOT).as_posix() for path in markdown if prose._scan_file(path)}
    assert not offenders, f"以下文档仍有口语命中：{sorted(offenders)}"
