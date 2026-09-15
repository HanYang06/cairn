# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

import pytest

from cairn.core import ObjectNotFoundError, Vault


def _vault(tmp_path: Path) -> Vault:
    return Vault.create(tmp_path / "vault")


def test_versions_placeholder_is_single_current(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put(b"one", type="blob")
    vault.put(b"two", oid=oid, type="blob")

    versions = vault.versions(oid)
    assert len(versions) == 1
    assert versions[0].seq == 1
    assert versions[0].is_current

    assert vault.read_version(oid, 1) == b"two"


def test_read_missing_version(tmp_path: Path) -> None:
    vault = _vault(tmp_path)
    oid = vault.put(b"x", type="blob")
    with pytest.raises(ObjectNotFoundError):
        vault.read_version(oid, 99)
