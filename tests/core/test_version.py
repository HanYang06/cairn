# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""版本引擎：id 口径与跨块根版本唯一性。"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core import Vault
from core.storage import VersionStore, version_id

if TYPE_CHECKING:
    from pathlib import Path


class _Codec:
    """最小 ``Codec``：签名取状态本身，补丁非空即「有变更」。"""

    def digest(self, state: Any) -> str:
        return str(state)

    def diff(self, new_state: Any, old_state: Any) -> bytes:
        return b"" if new_state == old_state else b"patch"

    def apply(self, _state: Any, _patch: Any) -> Any:
        raise NotImplementedError


def test_version_id_includes_oid() -> None:
    # 同一毫秒、同一签名、不同块 → 必须算出不同 id（否则插 version 撞主键）
    assert version_id("oid-a", None, 1000, "sig") != version_id("oid-b", None, 1000, "sig")


def test_roots_of_different_blocks_do_not_collide(tmp_path: Path) -> None:
    vault = Vault.create(tmp_path / "vault")
    store = VersionStore(vault.bucket)
    codec = _Codec()

    first = store.root("oid-a", codec, {"v": 1}, at=1000)
    second = store.root("oid-b", codec, {"v": 1}, at=1000)

    assert first is not None
    assert second is not None
    assert first != second
    assert store.head("oid-a") == first
    assert store.head("oid-b") == second
