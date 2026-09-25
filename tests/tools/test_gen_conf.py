# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`tools/gen_conf.py`：参数口径（写盘意图必须明确，未知参数不得被当成默认展开）。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import gen_conf  # noqa: E402


def test_unknown_argument_is_rejected() -> None:
    """拼错成 `-check` 之类的参数必须报错退出，不得静默走写盘分支。"""
    assert gen_conf.main(["-check"]) == 1
    assert gen_conf.main(["--chekc"]) == 1


def test_check_mode_is_read_only() -> None:
    """`--check` 在投影一致时返回 0（只读路径不写盘）。"""
    assert gen_conf.main(["--check"]) == 0
