# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记域组织器（`Facet`）：内容工具条 + 卡片舞台，并对外提供 `nav` / `page` 部件。

Facet 说领域话（`parts()`）；至于它们落到 App 的哪个槽，由 App 的槽 `expects` 决定。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ui_tools.component import Button, CardStage, Heading
from ui_tools.core import Facet
from ui_tools.layout import HBox, VBox

from ..backend import note_cards

if TYPE_CHECKING:
    from ui_tools.core import Session


class NoteFacet(Facet):
    """笔记域：工具条（视图形态）+ 卡片舞台 + 导航条目。"""

    def __init__(self, note: Any, session: Session) -> None:
        super().__init__(note, name="note")
        cards = session.model(lambda: note_cards(note))

        self.set(VBox)

        toolbar = self.add(HBox("toolbar"))
        toolbar.add(Heading("\u7b14\u8bb0", name="note_title"))
        self.density = toolbar.add(Button("\u25a4", name="density"))

        self.stage = self.add(
            CardStage(
                cards,
                title=lambda card: card.title,
                preview=lambda card: card.preview,
                meta=lambda card: card.meta,
                badge=lambda card: card.badge,
                name="stage",
            )
        )
        self.bind.add(self.density.clicked, self.stage.action("toggle_density"))

        self.nav = Button("\u7b14\u8bb0", name="nav_note")

    def parts(self) -> dict[str, object]:
        """提供 `page`（内容页）与 `nav`（导航条目）。"""
        return {"page": self.root, "nav": self.nav}


__all__ = ["NoteFacet"]
