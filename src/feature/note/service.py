# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记域服务 ``Note``：创建 / 读写 / 落盘 / 版本 / 关系 / 策略（**管数据**）。

数据（``NoteData``）由本服务与 Bucket 共同管理：Bucket 管存储，本服务管语义。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.signal import Domain, Topic, action
from core.storage import VersionStore

from ..shared.base import UNSET
from ..shared.signature import Signature
from .data import NoteData, access_ref, canvas_ref
from .edit import (
    Line as LineDict,
)
from .edit import (
    coerce_style,
    normalize_body,
)
from .model import NOTE_KIND
from .versions import NOTE_CODEC

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from core.types import Oid

    from ..shared.canvas import CanvasData


class Note(Domain):
    """笔记域服务（单例）：创建 / 读写 / 落盘 / 版本 / 关系 / 策略。"""

    name = "笔记"
    type = NOTE_KIND
    data = ("cairn.canvas", "cairn.asset")
    light = NoteData  # 最小数据单元（绑定既有类型，不复制字段）

    changed = Topic()

    def __init__(self, vault: Any) -> None:
        self.vault = vault

    # ---- 创建 / 读取 ----
    @action
    def create(
        self,
        text: str = "",
        *,
        title: str | None = None,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> NoteData:
        """新建一条笔记：落盘 + 记根版本，返回其数据。"""
        data = NoteData()
        data._vault = self.vault  # noqa: SLF001 — 服务为数据绑定库，同包强耦合
        data.set_text(text)
        data.title = title
        data.tags = tags or {}
        if props:
            data.attrs["props"] = dict(props)
        # 创作签名：锁在创建时的正文内容上（原始结构据此可找回）
        data.signature = Signature.create(author=data.author or "", subject=data.body_hash())
        self.save(data, search_text=_search_text(title, text))
        return data

    @action
    def load(self, oid: Oid | str) -> NoteData:
        """按 oid 载入一条笔记数据。"""
        data: NoteData = NoteData.load(self.vault, oid)
        data._saved_state = data._state()  # noqa: SLF001 — 记录落盘基线
        return data

    @action
    def list_notes(
        self,
        *,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
    ) -> list[NoteData]:
        """列出笔记数据。"""
        return [self.load(info.oid) for info in self.vault.iter(type=NOTE_KIND, tags=tags)]

    # ---- 落盘 / 版本 ----
    @action
    def save(self, data: NoteData, *, search_text: str | None = None) -> NoteData:
        """落盘并**记一个版本检查点**（内容变了才追加补丁）。"""
        if search_text is None:
            search_text = _search_text(data.title, data.text)
        previous = data._saved_state  # noqa: SLF001 — 域服务持有版本基线
        data.save(search_text=search_text)  # Block.save：块级落盘
        store = VersionStore(self.vault.bucket)
        if previous is None:
            store.root(data.id, NOTE_CODEC, data._state())  # noqa: SLF001
        else:
            current = data._state()  # noqa: SLF001
            if current != previous:
                store.commit(data.id, NOTE_CODEC, previous, current)
        data._saved_state = data._state()  # noqa: SLF001
        self.changed.emit(data.oid)
        return data

    @action
    def persist(self, data: NoteData, *, search_text: str | None = None) -> NoteData:
        """只**落盘当前内容**，不记版本（连续编辑中的自动保存用）。"""
        if search_text is None:
            search_text = _search_text(data.title, data.text)
        data.save(search_text=search_text)
        return data

    @action
    def history(self, data: NoteData) -> list[dict[str, Any]]:
        """版本历史（最新在前）。"""
        return VersionStore(self.vault.bucket).history(data.id)

    @action
    def body_at(self, data: NoteData, version: str) -> list[LineDict]:
        """取指定版本的正文行序列。"""
        state = VersionStore(self.vault.bucket).state_at(
            data.id,
            NOTE_CODEC,
            data._state(),  # noqa: SLF001 — 域服务读取数据内部状态
            str(version),
        )
        body: list[LineDict] = state["body"]
        return body

    @action
    def restore(self, data: NoteData, version: str) -> NoteData:
        """把指定版本的正文/样式作为新版本写回（历史继续向前）。"""
        state = VersionStore(self.vault.bucket).state_at(
            data.id,
            NOTE_CODEC,
            data._state(),  # noqa: SLF001 — 域服务读取数据内部状态
            str(version),
        )
        data.body.text = normalize_body(state["body"])
        data.body.style = coerce_style(state["style"], data.body.text)
        data.body.refresh()
        self.save(data)
        return data

    # ---- 属性 / 关系 / 嵌入 ----
    @action
    def update(
        self,
        data: NoteData,
        *,
        text: str | None = None,
        title: str | None = UNSET,
        tags: Iterable[str] | Mapping[str, Any] | None = None,
        props: dict[str, Any] | None = None,
    ) -> NoteData:
        """更新属性 / 正文并落盘记版本。"""
        merged = data.props()
        if props:
            merged.update(props)
        if title is not UNSET:
            data.title = title
        if tags is not None:
            data.tags = tags
        data.attrs["props"] = merged
        if text is not None:
            data.set_text(text)
        self.save(data, search_text=_search_text(data.title, data.text))
        return data

    @action
    def link(self, data: NoteData, target: Oid | str, relation: str = "references") -> Any:
        """从本笔记向目标建一条关系。"""
        from ..shared.relation import Relation  # noqa: PLC0415 — 延迟导入，避免领域间加载期环

        return Relation.create(self.vault, data.oid, target, relation=relation, domain="note")

    @action
    def add_canvas(self, data: NoteData, canvas: CanvasData) -> str:
        """把一块画板嵌进正文：``canvas`` 追加其 oid，并在 body 末尾放占位。"""
        entry = str(canvas.oid)
        data.canvas = [*data.canvas, entry]
        data._append_marker(canvas_ref(len(data.canvas) - 1))  # noqa: SLF001
        self.save(data)
        return entry

    @action
    def add_access(
        self,
        data: NoteData,
        oid: Oid | str,
        *,
        mime: str = "",
        name: str = "",
        size: float = 0.0,
    ) -> str:
        """把一段外联资源嵌进正文：``access`` 追加 asset 的 oid，body 末尾放占位。

        资源本体与其元数据都在 ``Asset`` 块里，这里只存引用。
        """
        del mime, name, size
        entry = str(oid)
        data.access = [*data.access, entry]
        data._append_marker(access_ref(len(data.access) - 1))  # noqa: SLF001
        self.save(data)
        return entry


def _search_text(title: str | None, text: str) -> str:
    return f"{title or ''}\n{text}"


__all__ = ["Note"]
