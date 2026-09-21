# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""最小类型表：域 / 数据结构的登记、字段 / 依赖 / 最小数据单元。"""

from __future__ import annotations

from core.signal import Domain
from core.types import ROLE_DATA, ROLE_DOMAIN, domain_of, type_info, types, unit_infos
from feature import CanvasData, Kind, Note, NoteData


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


def test_domain_units_point_at_data_types() -> None:
    info = type_info("cairn.note", role=ROLE_DOMAIN)

    assert info is not None
    assert info.units == ("cairn.note",)

    units = unit_infos("cairn.note")

    assert [unit.cls for unit in units] == [NoteData]
    assert "title" in units[0].fields


def test_domain_of_finds_owner_by_unit() -> None:
    owner = domain_of("cairn.note")

    assert owner is not None
    assert owner.cls is Note


def test_light_accepts_a_list_of_types() -> None:
    class Multi(Domain):
        name = "多单元"
        type = "cairn.test.multi"
        light = (NoteData, CanvasData)

    info = type_info("cairn.test.multi", role=ROLE_DOMAIN)

    assert info is not None
    assert info.units == ("cairn.note", "cairn.canvas")
    assert [unit.cls for unit in unit_infos("cairn.test.multi")] == [NoteData, CanvasData]


def test_degraded_structures_are_data_not_domain() -> None:
    for kind in ("cairn.canvas", "cairn.asset", "cairn.group"):
        assert type_info(kind, role=ROLE_DOMAIN) is None
        assert type_info(kind, role=ROLE_DATA) is not None


def test_project_is_domain() -> None:
    info = type_info("cairn.project", role=ROLE_DOMAIN)

    assert info is not None
    assert info.name == "项目"


def test_kind_enum_and_string_are_interchangeable() -> None:
    assert Kind.NOTE == "cairn.note"
    assert str(Kind.NOTE) == "cairn.note"

    assert type_info(Kind.NOTE, role=ROLE_DOMAIN) is not None
    assert type_info(Kind.NOTE, role=ROLE_DATA) is not None
    assert domain_of(Kind.NOTE) is not None
    assert Kind.NOTE in {info.type for info in types(ROLE_DOMAIN)}
    assert Kind.CANVAS in {info.type for info in types(ROLE_DATA)}


def test_types_filter_by_role() -> None:
    domains = {info.type for info in types(ROLE_DOMAIN)}
    data = {info.type for info in types(ROLE_DATA)}

    assert {"cairn.note", "cairn.project"} <= domains
    assert {"cairn.canvas", "cairn.asset", "cairn.group"} <= data
