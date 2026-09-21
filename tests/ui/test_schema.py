# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import pytest

from ui_tools.component import Component
from ui_tools.core import App, Facet, Schema, UiError, apply_config
from ui_tools.layout import Grid
from ui_tools.page import Page


class FakeDomain:
    pass


def _app() -> App:
    app = App(session=None)  # type: ignore[arg-type]
    facet = Facet(FakeDomain(), name="note")
    facet.set(Grid)
    facet.add(Component("title"))

    page = Page("edit")
    page.set(Grid)
    page.add(Component("editor"))
    facet.page(page, "edit")

    app.add(facet)
    return app


def test_schema_paths() -> None:
    paths = _app().schema().paths()

    assert "app.note" in paths
    assert "app.note.grid.title" in paths
    assert "app.note.edit" in paths
    assert "app.note.edit.grid.editor" in paths


def test_resolve_full_and_domain_rooted() -> None:
    schema = _app().schema()

    assert schema.resolve("app.note.edit.grid.editor") == "app.note.edit.grid.editor"
    assert schema.resolve("note.edit.grid.editor") == "app.note.edit.grid.editor"
    assert schema.resolve("edit.grid.editor") == "app.note.edit.grid.editor"


def test_resolve_unknown_raises() -> None:
    schema = _app().schema()

    with pytest.raises(UiError, match="未找到配置路径"):
        schema.resolve("note.nope")


def test_resolve_ambiguous_raises() -> None:
    schema = Schema()
    schema.add("app.a.shared")
    schema.add("app.b.shared")

    with pytest.raises(UiError, match="歧义"):
        schema.resolve("shared")


def test_apply_config_domain_rooted() -> None:
    schema = _app().schema()

    apply_config(schema, {"note.edit.grid.editor": {"color": "#fff"}})

    node = schema.node("note.edit.grid.editor")
    assert node is not None
    assert node.conf.attr.get("color") == "#fff"


def test_apply_config_theme_group() -> None:
    schema = _app().schema()

    apply_config(schema, {"note": {"token.accent": "#123456"}}, group="theme")

    node = schema.node("note")
    assert node is not None
    assert node.conf.theme.get("token.accent") == "#123456"


def test_apply_config_unknown_path_raises() -> None:
    schema = _app().schema()

    with pytest.raises(UiError, match="未找到配置路径"):
        apply_config(schema, {"note.nope": {"x": 1}})


def test_apply_config_bad_group_raises() -> None:
    schema = _app().schema()

    with pytest.raises(UiError, match="未知配置组"):
        apply_config(schema, {}, group="nope")


def test_node_unknown_returns_none() -> None:
    schema = _app().schema()

    assert schema.node("note.nope") is None


def test_contains_accepts_suffix_forms() -> None:
    schema = _app().schema()

    assert "note.edit.grid.editor" in schema
    assert "edit.grid.editor" in schema
    assert "note.nope" not in schema


def test_apply_config_rejects_non_mapping_items() -> None:
    schema = _app().schema()

    with pytest.raises(UiError, match="必须是映射"):
        apply_config(schema, {"note": 5})  # type: ignore[arg-type]


def test_apply_config_is_atomic() -> None:
    schema = _app().schema()

    with pytest.raises(UiError, match="未找到配置路径"):
        apply_config(schema, {"note": {"color": "#fff"}, "note.nope": {"x": 1}})

    node = schema.node("note")
    assert node is not None
    assert node.conf.attr.get("color") is None  # 坏路径让整批不落
