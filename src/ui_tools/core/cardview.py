# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""卡片视图：`Model` → 卡片 / 详细两种密度的 Qt 视图与委托。

属 Qt 边界（与 `qt.py` / `qtmodel.py` 同层）；颜色只取自 `Theme` 令牌，不硬编码。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPersistentModelIndex,
    QPointF,
    QRectF,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QListView,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QWidget,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from .model import Model
    from .theme import Theme

_NO_INDEX = QModelIndex()
ROLE_PREVIEW = int(Qt.ItemDataRole.UserRole) + 1
ROLE_META = int(Qt.ItemDataRole.UserRole) + 2
ROLE_BADGE = int(Qt.ItemDataRole.UserRole) + 3

_ALIGN_LEFT = int(Qt.AlignmentFlag.AlignLeft)
_ALIGN_RIGHT = int(Qt.AlignmentFlag.AlignRight)
_ALIGN_VCENTER = int(Qt.AlignmentFlag.AlignVCenter)
_ALIGN_TOP = int(Qt.AlignmentFlag.AlignTop)
_TEXT_WRAP = int(Qt.TextFlag.TextWordWrap)

_BADGE_TOKENS = {
    "notedata": "accent",
    "projectdata": "ochre",
    "canvas": "green",
    "asset": "green",
    "group": "ochre",
}


def _badge_color(theme: Theme, badge: str) -> QColor:
    """按徽标类型取令牌色（未知类型退回强调色，颜色只来自主题令牌）。"""
    return QColor(theme.token(_BADGE_TOKENS.get(badge, "accent")))


class QtCardModel(QAbstractListModel):
    """`Model[T]` → `QAbstractListModel`，用提取器映射到卡片各角色。"""

    def __init__(  # noqa: PLR0913 — 提取器是显式参数面
        self,
        model: Model[Any],
        *,
        title: Callable[[Any], str],
        preview: Callable[[Any], str],
        meta: Callable[[Any], str],
        badge: Callable[[Any], str],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._title = title
        self._preview = preview
        self._meta = meta
        self._badge = badge
        self._cancel = model.watch(self._reset)
        # C++ 对象被销毁时自动退订，避免回调打到已删除的 QObject。
        self.destroyed.connect(self._on_destroyed)

    def _on_destroyed(self, _obj: object = None) -> None:
        self.detach()

    def _reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def rowCount(  # noqa: N802 — Qt 覆写
        self,
        parent: QModelIndex | QPersistentModelIndex = _NO_INDEX,
    ) -> int:
        del parent
        return len(self._model)

    def data(
        self,
        index: QModelIndex | QPersistentModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None
        row = index.row()
        if not 0 <= row < len(self._model):
            return None
        item = self._model[row]
        result: Any = None
        if role == Qt.ItemDataRole.DisplayRole:
            result = self._title(item)
        elif role in (int(Qt.ItemDataRole.ToolTipRole), ROLE_PREVIEW):
            result = self._preview(item)
        elif role == ROLE_META:
            result = self._meta(item)
        elif role == ROLE_BADGE:
            result = self._badge(item)
        return result

    def detach(self) -> None:
        """断开对 `Model` 的观察。"""
        self._cancel()


class _RoundedMixin:
    """委托共用：圆角面 + 悬停 / 选中的颜色归属，全部取自令牌。"""

    _theme: Theme

    def _surface(self, option: QStyleOptionViewItem, *, base: str = "elevated") -> tuple[str, str]:
        if option.state & QStyle.StateFlag.State_Selected:
            return self._theme.token("accent_soft"), self._theme.token("accent")
        if option.state & QStyle.StateFlag.State_MouseOver:
            return self._theme.token("hover"), self._theme.token("border")
        return self._theme.token(base), self._theme.token("border_soft")


class CardDelegate(_RoundedMixin, QStyledItemDelegate):
    """卡片密度：圆角卡 + 徽标色点 + 标题 / 摘要 / 时间。"""

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme

    def sizeHint(  # noqa: N802 — Qt 覆写
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        del option, index
        return QSize(240, 140)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect).adjusted(5.0, 5.0, -5.0, -5.0)
        fill, edge = self._surface(option)
        path = QPainterPath()
        path.addRoundedRect(rect, 14.0, 14.0)
        painter.fillPath(path, QColor(fill))
        pen = QPen(QColor(edge))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(_badge_color(self._theme, str(index.data(ROLE_BADGE) or "note")))
        painter.drawEllipse(QPointF(rect.left() + 17.0, rect.top() + 19.0), 4.5, 4.5)

        title_font = QFont(option.font)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.setPen(QColor(self._theme.token("text")))
        painter.drawText(
            QRectF(rect.left() + 32.0, rect.top() + 10.0, rect.width() - 46.0, 22.0),
            _ALIGN_LEFT | _ALIGN_VCENTER,
            option.fontMetrics.elidedText(
                str(index.data() or ""),
                Qt.TextElideMode.ElideRight,
                int(rect.width() - 46.0),
            ),
        )

        painter.setFont(option.font)
        painter.setPen(QColor(self._theme.token("muted")))
        painter.drawText(
            QRectF(rect.left() + 14.0, rect.top() + 44.0, rect.width() - 28.0, 50.0),
            _ALIGN_LEFT | _ALIGN_TOP | _TEXT_WRAP,
            str(index.data(ROLE_PREVIEW) or ""),
        )

        painter.setPen(QColor(self._theme.token("faint")))
        painter.drawText(
            QRectF(rect.left() + 14.0, rect.bottom() - 24.0, rect.width() - 28.0, 18.0),
            _ALIGN_RIGHT | _ALIGN_VCENTER,
            str(index.data(ROLE_META) or ""),
        )
        painter.restore()


class RowDelegate(_RoundedMixin, QStyledItemDelegate):
    """详细密度：单行 + 徽标 + 时间。"""

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._theme = theme

    def sizeHint(  # noqa: N802 — Qt 覆写
        self,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> QSize:
        del index
        width = option.widget.width() if option.widget is not None else 260
        return QSize(max(width - 8, 120), 38)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionViewItem,
        index: QModelIndex | QPersistentModelIndex,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(option.rect).adjusted(4.0, 2.0, -4.0, -2.0)
        fill, _edge = self._surface(option, base="surface")
        path = QPainterPath()
        path.addRoundedRect(rect, 8.0, 8.0)
        painter.fillPath(path, QColor(fill))

        painter.setPen(QColor(self._theme.token("faint")))
        painter.drawText(
            QRectF(rect.right() - 96.0, rect.top(), 88.0, rect.height()),
            _ALIGN_RIGHT | _ALIGN_VCENTER,
            str(index.data(ROLE_META) or ""),
        )

        chip = QRectF(rect.right() - 132.0, rect.center().y() - 9.0, 34.0, 18.0)
        chip_path = QPainterPath()
        chip_path.addRoundedRect(chip, 9.0, 9.0)
        painter.fillPath(
            chip_path,
            _badge_color(self._theme, str(index.data(ROLE_BADGE) or "note")),
        )

        painter.setPen(QColor(self._theme.token("text")))
        painter.drawText(
            QRectF(rect.left() + 16.0, rect.top(), rect.width() - 168.0, rect.height()),
            _ALIGN_LEFT | _ALIGN_VCENTER,
            option.fontMetrics.elidedText(
                str(index.data() or ""),
                Qt.TextElideMode.ElideRight,
                int(rect.width() - 168.0),
            ),
        )
        painter.restore()


class CardStageView(QListView):
    """卡片 / 详细两种密度的舞台（同一模型）。"""

    def __init__(  # noqa: PLR0913 — 提取器 + 密度是显式参数面
        self,
        model: Model[Any],
        theme: Theme,
        *,
        title: Callable[[Any], str],
        preview: Callable[[Any], str],
        meta: Callable[[Any], str],
        badge: Callable[[Any], str],
        density: str = "cards",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("cairnClass", "stage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, on=True)
        self.setModel(
            QtCardModel(model, title=title, preview=preview, meta=meta, badge=badge, parent=self)
        )
        self._card_delegate = CardDelegate(theme, self)
        self._row_delegate = RowDelegate(theme, self)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.viewport().setAutoFillBackground(False)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.set_dense(dense=density == "details")

    def toggle_density(self) -> None:
        """在卡片 / 详细两密度间切换。"""
        self.set_dense(dense=self.viewMode() == QListView.ViewMode.IconMode)

    def set_dense(self, *, dense: bool) -> None:
        """切密度：`True` = 详细列表，`False` = 卡片网格。"""
        if dense:
            self.setViewMode(QListView.ViewMode.ListMode)
            self.setItemDelegate(self._row_delegate)
            self.setSpacing(2)
            self.setUniformItemSizes(False)
            self.setWrapping(False)
            self.setFlow(QListView.Flow.TopToBottom)
            self.setResizeMode(QListView.ResizeMode.Adjust)
            self.setGridSize(QSize())
        else:
            self.setViewMode(QListView.ViewMode.IconMode)
            self.setItemDelegate(self._card_delegate)
            self.setSpacing(6)
            self.setUniformItemSizes(False)
            self.setMovement(QListView.Movement.Static)
            self.setFlow(QListView.Flow.LeftToRight)
            self.setWrapping(True)
            self.setResizeMode(QListView.ResizeMode.Adjust)
            self.setGridSize(QSize(248, 150))


__all__ = [
    "ROLE_BADGE",
    "ROLE_META",
    "ROLE_PREVIEW",
    "CardDelegate",
    "CardStageView",
    "QtCardModel",
    "RowDelegate",
]
