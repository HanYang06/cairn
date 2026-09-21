# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Qt-free 列表模型：类型化数据 + 变更通知。

UI 的列表 / 投影都落在它上面；Qt 模型（`QAbstractItemModel`）在桥接层包它，
不在这里依赖 Qt。
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Iterator

type Notify = Callable[[], None]

_log = logging.getLogger(__name__)


class Model[T]:
    """类型化可观察列表。"""

    def __init__(self, items: Iterable[T] = ()) -> None:
        self._items: list[T] = list(items)
        self._observers: list[Notify] = []

    def items(self) -> list[T]:
        """当前数据（副本）。"""
        return list(self._items)

    def __getitem__(self, index: int) -> T:
        """按下标取一项（不复制整表，供 Qt 委托热路径用）。"""
        return self._items[index]

    def replace(self, items: Iterable[T]) -> None:
        """整体替换并通知；内容一致时跳过。"""
        new_items = list(items)
        if new_items == self._items:
            return
        self._items = new_items
        self._notify()

    def append(self, item: T) -> None:
        """追加一项并通知。"""
        self._items.append(item)
        self._notify()

    def remove(self, item: T) -> None:
        """移除一项并通知（不存在则不动）。"""
        if item in self._items:
            self._items.remove(item)
            self._notify()

    def clear(self) -> None:
        """清空并通知（本已为空则不动）。"""
        if not self._items:
            return
        self._items.clear()
        self._notify()

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[T]:
        return iter(list(self._items))

    def watch(self, callback: Notify) -> Notify:
        """观察变更；返回取消函数（重复注册去重，取消移除全部匹配）。"""
        if callback not in self._observers:
            self._observers.append(callback)

        def cancel() -> None:
            self._observers[:] = [item for item in self._observers if item != callback]

        return cancel

    def _notify(self) -> None:
        for callback in list(self._observers):
            try:
                callback()
            except Exception:  # noqa: BLE001 — 单个观察者失败不应中断其余通知
                _log.exception("模型观察者执行失败")

    def __repr__(self) -> str:
        return f"Model({len(self._items)})"


__all__ = ["Model", "Notify"]
