# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""富文本编辑器：`NoteDocument` 映射 + `NoteEditor` 控件 + 扩展点（`formats`）。"""

from __future__ import annotations

from .document import NoteDocument
from .editor import NoteEditor

__all__ = ["NoteDocument", "NoteEditor"]
