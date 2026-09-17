# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""把主题令牌渲染成 QSS。一个模板，服务所有主题。

约定：组件只提供 `objectName` / 类名，样式一律由这里统一给出，不各自 `setStyleSheet`。
"""

from __future__ import annotations

from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from .loader import ThemeFile
    from .tokens import Theme

_QSS = Template(
    """
QWidget {
    background-color: $bg;
    color: $text;
    font-family: "$font_family";
    font-size: ${fs_body}px;
}
QMainWindow, QDialog { background-color: $bg; }
QMainWindow::separator { background: $border_faint; width: 1px; height: 1px; }

QLabel#Muted { color: $muted; }
QLabel#Faint { color: $faint; }
QLabel#PanelTitle {
    color: $text;
    font-size: ${fs_small}px;
    font-weight: 600;
    padding: ${space_sm}px ${space_md}px;
}

QFrame#Card {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: ${radius_lg}px;
}
QFrame#Divider { background: $border_faint; max-height: 1px; }

QListView, QTreeView, QTableView {
    background-color: $surface;
    border: none;
    outline: none;
    show-decoration-selected: 1;
}
QListView::item, QTreeView::item, QTableView::item {
    padding: ${space_sm}px;
    border-radius: ${radius_sm}px;
}
QListView::item:hover, QTreeView::item:hover { background-color: $hover; }
QListView::item:selected, QTreeView::item:selected {
    background-color: $selection;
    color: $text;
}
QHeaderView::section {
    background-color: $surface;
    color: $muted;
    border: none;
    border-bottom: 1px solid $border_faint;
    padding: ${space_sm}px;
}

QPushButton, QToolButton {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: ${radius}px;
    padding: ${space_xs}px ${space_sm}px;
}
QPushButton:hover, QToolButton:hover { border-color: $accent; }
QPushButton:pressed, QToolButton:pressed { background-color: $hover; }
QPushButton#Primary {
    background-color: $accent;
    color: $accent_text;
    border: none;
}

QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: ${radius}px;
    padding: ${space_sm}px;
    selection-background-color: $accent;
    selection-color: $accent_text;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus { border-color: $accent; }

QMenuBar { background-color: $chrome; }
QMenuBar::item { padding: ${space_xs}px ${space_sm}px; background: transparent; }
QMenuBar::item:selected { background-color: $hover; border-radius: ${radius_sm}px; }
QMenu { background-color: $elevated; border: 1px solid $border; padding: ${space_xs}px; }
QMenu::item { padding: ${space_xs}px ${space_lg}px; border-radius: ${radius_sm}px; }
QMenu::item:selected { background-color: $selection; }

QSplitter::handle { background: transparent; }
QSplitter::handle:hover { background: $border; }

QStatusBar {
    background-color: $chrome;
    color: $muted;
    border-top: 1px solid $border_faint;
}
QToolTip {
    background-color: $elevated;
    color: $text;
    border: 1px solid $border;
    padding: ${space_xs}px ${space_sm}px;
}

QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical {
    background: $border;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: $muted; }
QScrollBar:horizontal { background: transparent; height: 10px; margin: 0; }
QScrollBar::handle:horizontal {
    background: $border;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
""".lstrip()
)


def build_qss(theme: Theme) -> str:
    """用令牌渲染 QSS；缺令牌会显式报错。"""
    return _QSS.substitute(theme.as_dict())


# 主题 DSL 的属性名 → QSS 属性名。
_QSS_PROPERTY = {
    "background": "background-color",
    "color": "color",
    "border": "border",
    "border_color": "border-color",
    "radius": "border-radius",
    "padding": "padding",
    "font_size": "font-size",
    "font_weight": "font-weight",
}


def _resolve(theme: Theme, value: str) -> str:
    """把 ``token.<字段>`` 引用解成令牌值；其余原样。"""
    if value.startswith("token."):
        return str(getattr(theme, value[len("token.") :]))
    return value


def build_widget_qss(theme: Theme, rules: Mapping[str, str]) -> str:
    """把部件点分规则编译成 QSS（选择器用动态属性 ``cairnClass``）。"""
    grouped: dict[str, list[str]] = {}
    for path, raw in sorted(rules.items()):
        parts = path.split(".")
        if len(parts) not in (3, 4) or parts[0] != "widget":
            continue
        type_name = parts[1]
        state = parts[2] if len(parts) == 4 else ""
        css = _QSS_PROPERTY.get(parts[-1])
        if css is None:
            continue
        selector = f'QWidget[cairnClass="{type_name}"]' + (f":{state}" if state else "")
        grouped.setdefault(selector, []).append(f"    {css}: {_resolve(theme, raw)};")
    return "\n".join(
        f"{selector} {{\n" + "\n".join(body) + "\n}" for selector, body in grouped.items()
    )


def compile_theme(theme_file: ThemeFile) -> str:
    """编译一个主题包：令牌 QSS + 部件规则 QSS。"""
    parts = [build_qss(theme_file.theme)]
    widget_qss = build_widget_qss(theme_file.theme, theme_file.rules)
    if widget_qss:
        parts.append(widget_qss)
    return "\n".join(parts)


__all__ = ["build_qss", "build_widget_qss", "compile_theme"]
