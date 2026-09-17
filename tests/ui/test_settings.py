# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""UI 设置存储测试：点分键、落盘、合并。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cairn.ui.settings import SettingsStore

if TYPE_CHECKING:
    from pathlib import Path


def test_dot_path_roundtrip(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path)
    assert store.get("a.b", 1) == 1
    store.set("a.b", 2)
    assert store.get("a.b") == 2
    assert store.path == tmp_path / ".cairn" / "ui.json"


def test_persist_across_instances(tmp_path: Path) -> None:
    SettingsStore(tmp_path).set("window.theme", "github-dark")
    assert SettingsStore(tmp_path).get("window.theme") == "github-dark"


def test_merge_keeps_siblings(tmp_path: Path) -> None:
    store = SettingsStore(tmp_path)
    store.merge({"x": {"y": 1}})
    store.merge({"x": {"z": 2}})
    assert store.get("x.y") == 1
    assert store.get("x.z") == 2
