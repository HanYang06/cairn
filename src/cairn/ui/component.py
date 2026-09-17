# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Component`：所有 UI 部件的基类（中性位置，供组件 / 布局 / 页面共用）。

放在 `ui/` 顶层而非 `components/`，是为了避免「布局 ↔ 组件」的循环依赖：
布局原语也用 `Component`，但它们本身不算组件。注册表只收 `cairn.ui.components`
下的具体部件，布局 / 页面不入主题词汇表。
"""

from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING, Any, ClassVar

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget

from .signal import Subscription
from .theme import Theme, current_theme

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

# 只有标准组件库里的部件进入主题词汇表；布局 / 页面 / 外壳 / 测试类不污染 schema。
_COMPONENT_PACKAGE = "cairn.ui.components"


class Component(QWidget):
    """所有 UI 部件的基类：令牌访问、命名约定、生命周期订阅、**继承注册表**。

    注册表照搬内核 ``Block`` 的做法：子类定义即入册，供主题 schema 自动生成词汇表。
    子类用 ``STYLABLE`` / ``STATES`` 声明自己可被主题描述的范围；``abstract = True`` 的
    中间基类不入册。
    """

    _REGISTRY: ClassVar[dict[str, type[Component]]] = {}
    abstract: ClassVar[bool] = False
    STYLABLE: ClassVar[frozenset[str]] = frozenset(
        {"background", "color", "border", "border_color", "radius", "padding"}
    )
    STATES: ClassVar[frozenset[str]] = frozenset({"hover", "pressed", "disabled", "focus"})

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__dict__.get("abstract", False):
            return
        if not cls.__module__.startswith(_COMPONENT_PACKAGE):
            return
        Component._REGISTRY[cls.__name__] = cls

    @classmethod
    def registry(cls) -> Mapping[str, type[Component]]:
        """已注册的具体部件：``{类名: 类}``（主题 schema 的词汇表）。"""
        return dict(cls._REGISTRY)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # 让纯 QWidget 子类也能被 QSS 背景命中（否则背景不绘制）。
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)  # noqa: FBT003 — Qt API
        self._watchers: list[tuple[Any, Any]] = []
        self.destroyed.connect(self._cancel_watchers)
        if not self.objectName():
            self.setObjectName(type(self).__name__)
        # 供主题 QSS 以属性选择器命中：QWidget[cairnClass="Button"]
        self.setProperty("cairnClass", type(self).__name__)

    @property
    def theme(self) -> Theme:
        """当前主题令牌；组件样式一律取自这里，不硬编码。"""
        return current_theme()

    def watch(self, source: Any, slot: Callable[..., None]) -> None:
        """订阅一个信号（Qt 信号或 `ui.signal.Signal`）；控件销毁时自动退订。"""
        connection = source.connect(slot)
        self._watchers.append((source, connection))

    def _cancel_watchers(self, *_args: object) -> None:
        for source, connection in self._watchers:
            if isinstance(connection, Subscription):
                connection.cancel()
            else:
                with suppress(Exception):
                    source.disconnect(connection)
        self._watchers.clear()


__all__ = ["Component"]
