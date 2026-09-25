# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""Windows 根壳：Cairn 的根。自己组织根本布局（大方框 + 格子 + 槽），再把领域组织器加进来。

只对使用者暴露两件事：`CairnApp.open()`（开库 + 组装）与 `.run()`（跑起来）。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from core.core import Core
from ui_tools.component import Button, Field, Heading, Label, Surface
from ui_tools.core import App, Session, Slot
from ui_tools.core.qt import run as run_app
from ui_tools.layout import HBox

from ... import Feature
from .notes import NoteFacet
from .theme import app_theme

if TYPE_CHECKING:
    from ui_tools.core import Theme


def _default_root() -> Path:
    """库根：`CAIRN_VAULT` 优先（空白视为未设），否则 `<cwd>/vault`。"""
    raw = os.environ.get("CAIRN_VAULT")
    if raw and raw.strip():
        return Path(raw.strip())
    return Path.cwd() / "vault"


class CairnApp(App):
    """Cairn 的根：自己搭的一个大方框（顶带 / 主体 / 底栏），主体里开两个槽。"""

    def __init__(self, core: Core, *, theme: Theme | None = None) -> None:
        # 域服务受内核管辖：这里只取用（没有才建）
        feature = Feature(core)
        active_theme = theme or app_theme()  # 先建主题（可能失败），再发布 Feature
        super().__init__(Session(core.signal), theme=active_theme)
        self._core = core

        root = self.root

        top = root.add(Surface(name="top", orientation="h", elevated=True))
        top.add(Heading("\u26f0  Cairn", name="brand"))
        top.add(Field(placeholder="\u641c\u7d22 / \u547d\u4ee4", name="search", stretch=True))
        top.add(Button("\u22ef", name="more"))

        body = root.add(HBox("body", stretch=True))
        body.add(Slot("nav", expects="nav", align="top"))
        body.add(Slot("main", expects="page", stretch=True))

        bottom = root.add(Surface(name="bottom", orientation="h"))
        bottom.add(Heading("\u4efb\u52a1", name="task_title"))
        bottom.add(Label("\u6682\u65e0\u540e\u53f0\u4efb\u52a1", name="hint"))

        self.add(NoteFacet(feature.Note, self.session))

    @classmethod
    def open(cls, root: Path | None = None) -> CairnApp:
        """开库 + 组装：无目录则创建，否则加载（加载失败如实抛出，不掩盖）。

        默认读 `CAIRN_VAULT` 或 `<cwd>/vault`。内核是单例：拿到它就拿到全部。
        """
        path = root or _default_root()
        core = Core()
        core.open(path)  # 已存在的库：版本 / 配置错误应向外传播，不掩盖
        return cls(core)

    def close(self) -> None:
        """关闭底层库（释放 catalog 连接）。"""
        self._core.close()

    def run(self) -> int:
        """跑起来：套主题、建窗、进事件循环。"""
        return run_app(self)


__all__ = ["CairnApp"]
