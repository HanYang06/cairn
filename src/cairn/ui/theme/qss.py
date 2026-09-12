# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""把主题令牌渲染成 QSS。一个模板，服务所有主题。"""

from __future__ import annotations

from string import Template

from .tokens import Theme

_QSS = Template(
    """
QWidget {
    background-color: $bg;
    color: $text;
    font-family: "$font_family";
    font-size: ${font_size}pt;
}
QMainWindow, QDialog { background-color: $bg; }
QFrame#Card {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: ${radius_card}px;
}
QListWidget, QListView, QTreeView {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: ${radius}px;
    outline: none;
}
QListWidget::item, QListView::item {
    padding: ${spacing}px;
    border-radius: ${radius}px;
}
QListWidget::item:selected, QListView::item:selected {
    background-color: $selection;
    color: $text;
}
QPushButton {
    background-color: $elevated;
    border: 1px solid $border;
    border-radius: ${radius}px;
    padding: ${spacing}px;
}
QPushButton:hover { border-color: $accent; }
QPushButton#Primary {
    background-color: $accent;
    color: $on_accent;
    border: none;
}
QLineEdit, QPlainTextEdit, QTextEdit {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: ${radius}px;
    padding: ${spacing}px;
    selection-background-color: $accent;
    selection-color: $on_accent;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus { border-color: $accent; }
QLabel#Muted { color: $muted; }
QToolTip {
    background-color: $elevated;
    color: $text;
    border: 1px solid $border;
}
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical {
    background: $border;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: $muted; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
""".lstrip()
)


def build_qss(theme: Theme) -> str:
    """用令牌渲染 QSS；缺令牌会显式报错。"""
    return _QSS.substitute(theme.as_dict())
