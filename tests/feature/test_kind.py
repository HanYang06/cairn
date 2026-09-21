# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""最小类型表：域 / 数据结构的登记与字段 / 依赖元数据。"""

from __future__ import annotations

from core.types import ROLE_DATA, ROLE_DOMAIN, type_info, types
from feature import Note, NoteData


def test_domain_and_data_share_type_but_differ_by_role() -> None:
    domain = type_info("cairn.note", role=ROLE_DOMAIN)
    data = type_info("cairn.note", role=ROLE_DATA)

    assert domain is not None
    assert data is not None
    assert domain.cls is Note
    assert data.cls is NoteData
    assert domain.role == ROLE_DOMAIN
    assert data.role == ROLE_DATA


def test_type_info_defaults_to_domain() -> None:
    info = type_info("cairn.note")

    assert info is not None
    assert info.role == ROLE_DOMAIN
    assert info.name == "笔记"
    assert info.deps == ("cairn.canvas", "cairn.asset")


def test_data_fields_registered() -> None:
    info = type_info("cairn.note", role=ROLE_DATA)

    assert info is not None
    assert "title" in info.fields
    assert "tags" in info.fields


def test_degraded_structures_are_data_not_domain() -> None:
    for kind in ("cairn.canvas", "cairn.asset", "cairn.group"):
        assert type_info(kind, role=ROLE_DOMAIN) is None
        assert type_info(kind, role=ROLE_DATA) is not None


def test_project_is_domain() -> None:
    info = type_info("cairn.project", role=ROLE_DOMAIN)

    assert info is not None
    assert info.name == "项目"


def test_types_filter_by_role() -> None:
    domains = {info.type for info in types(ROLE_DOMAIN)}
    data = {info.type for info in types(ROLE_DATA)}

    assert {"cairn.note", "cairn.project"} <= domains
    assert {"cairn.canvas", "cairn.asset", "cairn.group"} <= data
