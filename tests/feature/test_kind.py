# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""最小类型表：域 / 数据结构的登记、字段 / 依赖 / 最小数据单元。"""

from __future__ import annotations

from enum import Enum

import pytest

from core.core import Managed
from core.types import (
    ROLE_DATA,
    ROLE_DOMAIN,
    TypeInfo,
    domain_of,
    register,
    type_info,
    types,
    unit_infos,
)
from feature import CanvasData, Kind, Note, NoteData


def test_domain_and_data_have_distinct_types() -> None:
    domain = type_info(Kind.Feature.Note, role=ROLE_DOMAIN)
    data = type_info(Kind.Data.Notedata, role=ROLE_DATA)

    assert domain is not None
    assert data is not None
    assert domain.cls is Note
    assert data.cls is NoteData
    assert domain.type == "note"
    assert data.type == "notedata"


def test_type_info_defaults_to_domain() -> None:
    info = type_info("note")

    assert info is not None
    assert info.role == ROLE_DOMAIN
    assert info.name == "note"
    assert info.deps == ("notedata", "asset", "canvas", "group")


def test_data_fields_registered() -> None:
    info = type_info(Kind.Data.Notedata, role=ROLE_DATA)

    assert info is not None
    assert "title" in info.fields
    assert "tags" in info.fields


def test_domain_units_point_at_data_types() -> None:
    info = type_info(Kind.Feature.Note, role=ROLE_DOMAIN)

    assert info is not None
    assert info.units == ("notedata",)

    units = unit_infos(Kind.Feature.Note)

    assert [unit.cls for unit in units] == [NoteData]
    assert "title" in units[0].fields


def test_domain_of_finds_owner_by_unit() -> None:
    owner = domain_of(Kind.Data.Notedata)

    assert owner is not None
    assert owner.cls is Note


def test_light_accepts_a_list_of_types() -> None:
    class Multi(Managed):
        name = "多单元"
        type = "test.multi"
        light = (NoteData, CanvasData)

    info = type_info("test.multi", role=ROLE_DOMAIN)

    assert info is not None
    assert info.units == ("notedata", "canvas")
    assert [unit.cls for unit in unit_infos("test.multi")] == [NoteData, CanvasData]


def test_register_normalizes_type_and_units() -> None:
    class Demo(Enum):
        One = "test.reg"

    register(
        TypeInfo(
            type=Demo.One,  # type: ignore[arg-type] — 刻意喂枚举，验证登记口会归一
            role=ROLE_DOMAIN,
            cls=Note,
            units=(Demo.One,),  # type: ignore[arg-type]
        )
    )

    info = type_info("test.reg", role=ROLE_DOMAIN)

    assert info is not None
    assert info.type == "test.reg"
    assert info.units == ("test.reg",)


def test_unit_infos_rejects_unregistered_unit() -> None:
    register(TypeInfo(type="test.broken", role=ROLE_DOMAIN, cls=Note, units=("nope",)))

    with pytest.raises(LookupError, match="未登记"):
        unit_infos("test.broken")


def test_degraded_structures_are_data_not_domain() -> None:
    for kind in (Kind.Data.Canvas, Kind.Data.Asset, Kind.Data.Group):
        assert type_info(kind, role=ROLE_DOMAIN) is None
        assert type_info(kind, role=ROLE_DATA) is not None


def test_project_is_domain() -> None:
    info = type_info(Kind.Feature.Project, role=ROLE_DOMAIN)

    assert info is not None
    assert info.name == "project"


def test_kind_values_are_short_names() -> None:
    assert Kind.Feature.Note.value == "note"
    assert Kind.Data.Notedata.value == "notedata"
    assert type_info("notedata", role=ROLE_DATA) is not None


def test_types_filter_by_role() -> None:
    domains = {info.type for info in types(ROLE_DOMAIN)}
    data = {info.type for info in types(ROLE_DATA)}

    assert {"note", "project"} <= domains
    assert {"canvas", "asset", "group"} <= data
