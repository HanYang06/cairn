# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

import pytest

from cairn.core import ObjectNotFoundError, Vault


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault", "pw")


def test_versions_and_restore(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put(b"one", type="blob")
    vault.put(b"two", oid=oid, type="blob")
    vault.put(b"three", oid=oid, type="blob")

    versions = vault.versions(oid)
    assert [item.seq for item in versions] == [3, 2, 1]
    assert versions[0].is_current
    assert not versions[1].is_current

    with vault.open(oid) as handle:
        assert handle.read() == b"three"
    assert vault.read_version(oid, 1) == b"one"
    assert vault.read_version(oid, 2) == b"two"

    vault.restore_version(oid, 1)
    assert [item.seq for item in vault.versions(oid)] == [4, 3, 2, 1]
    with vault.open(oid) as handle:
        assert handle.read() == b"one"


def test_read_missing_version(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put(b"x", type="blob")
    with pytest.raises(ObjectNotFoundError):
        vault.read_version(oid, 99)
