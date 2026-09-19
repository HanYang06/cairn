# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置系统测试：默认 / 覆盖 / 重定向 / 失效 / 未知。"""

from __future__ import annotations

import pytest

from cairn.ui.decl import Component, UiConfAttribute, UiConfError, collect_schema


class Widget(Component):
    kind = "test-widget"

    size = UiConfAttribute[int](default=1)
    label = UiConfAttribute[str](default="x")


class Fancy(Widget):
    kind = "test-fancy"

    size = UiConfAttribute[int](default=2)
    color = UiConfAttribute[str](default="red")
    label = UiConfAttribute[str](redirect="caption")
    caption = UiConfAttribute[str](default="cap")


class Locked(Widget):
    kind = "test-locked"

    size = UiConfAttribute[int](invalidated=True)


def test_defaults_from_schema() -> None:
    widget = Widget()
    assert widget.size == 1
    assert widget.label == "x"
    assert widget.enabled is True
    assert widget.tooltip == ""


def test_provided_value_overrides_default() -> None:
    assert Widget(size=5).size == 5


def test_subclass_override_default() -> None:
    assert Fancy().size == 2
    assert Fancy().color == "red"


def test_redirect_alias_reads_and_writes_target() -> None:
    fancy = Fancy(label="hi")
    assert fancy.caption == "hi"
    assert fancy.label == "hi"


def test_redirect_alias_falls_back_to_target_default() -> None:
    assert Fancy().label == "cap"


def test_collect_schema_includes_inherited_and_base() -> None:
    schema = collect_schema(Widget)
    assert {"size", "label", "enabled", "tooltip"} <= set(schema)


def test_unknown_attribute_errors() -> None:
    with pytest.raises(UiConfError):
        Widget(bogus=1)


def test_invalidated_read_errors() -> None:
    with pytest.raises(UiConfError):
        Locked().size  # noqa: B018 — 触发描述符
    with pytest.raises(UiConfError):
        Locked(size=9)


def test_invalidated_write_errors() -> None:
    with pytest.raises(UiConfError):
        Locked().size = 5


def test_class_access_returns_descriptor() -> None:
    assert isinstance(Widget.size, UiConfAttribute)
