# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""`Session`：内核状态在 UI 侧的**只读镜像**（Qt-free）。

职责：
- 订阅内核事件，把「哪一块变了」记下来，并作废投影缓存；
- 提供类型化的投影（当前是笔记行）；
- 用极简 `Signal` 广播变更，交给桥接层翻译成 Qt 信号。

不缓存可变领域对象（编辑中的实例由编辑器自己持有），避免与写入互相打架。
"""

from __future__ import annotations

from ..core import Event, ObjectDeleted, ObjectPut, Vault
from ..domains import Note, ancestors, descendants
from ..domains.group import Group
from .format import fmt_size, fmt_time
from .rows import GroupNode, NoteRow, PropertyRow, RelationRow, VersionRow
from .signal import Cancellable, Signal

VAULT_LABEL = "个人空间"


def _short_signature(signature: object) -> str:
    value = str(getattr(signature, "value", "") or "")
    if not value:
        return "—"
    alg = str(getattr(signature, "alg", "") or "")
    head = value[:10] + "…"
    return f"{alg} · {head}" if alg else head


class Session:
    """内核状态镜像：投影缓存 + 变更信号。"""

    def __init__(self, vault: Vault) -> None:
        self._vault = vault
        self._rows: list[NoteRow] | None = None
        self._changed: set[str] = set()
        self.changed = Signal()
        self._subscriptions: list[Cancellable] = [
            vault.subscribe(self._on_event, event_type=ObjectPut),
            vault.subscribe(self._on_event, event_type=ObjectDeleted),
        ]

    @property
    def vault(self) -> Vault:
        """底层库（facade / 编辑器需要写时用）。"""
        return self._vault

    # ---- 读投影 ----
    def note_rows(self) -> list[NoteRow]:
        """笔记行投影（按更新时间倒序），带缓存，事件驱动作废。"""
        if self._rows is None:
            self._rows = self._build_rows()
        return list(self._rows)

    def note(self, oid: str) -> Note:
        """按需加载一篇笔记（用于编辑，不进缓存）。"""
        return Note.load(self._vault, oid)

    def note_properties(self, oid: str) -> list[PropertyRow]:
        """把一篇笔记投影成检查器的属性行。"""
        try:
            note = self.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return []
        props = note.props()
        info = note.info
        return [
            PropertyRow("kind", "类型", "笔记", "text", editable=False),
            PropertyRow("vault", "库", VAULT_LABEL, "text", editable=False),
            PropertyRow("author", "作者", note.author or "—", "text", editable=False),
            PropertyRow(
                "signature", "签名", _short_signature(note.signature), "text", editable=False
            ),
            PropertyRow(
                "tags",
                "标签",
                "、".join(str(key) for key in note.tags) or "—",
                "text",
                editable=False,
            ),
            PropertyRow("favorite", "收藏", bool(props.get("favorite")), "bool", editable=True),
            PropertyRow("archived", "归档", bool(props.get("archived")), "bool", editable=True),
            PropertyRow("created", "创建", fmt_time(int(info.created)), "text", editable=False),
            PropertyRow("updated", "修改", fmt_time(int(info.updated)), "text", editable=False),
            PropertyRow("words", "字数", len(note.text), "count", editable=False),
            PropertyRow("size", "大小", fmt_size(int(info.size)), "text", editable=False),
        ]

    def relation_rows(self, oid: str) -> list[RelationRow]:
        """关系视图投影：上游（来源）+ 当前 + 下游（派生）。"""
        try:
            note = self.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return []
        rows: list[RelationRow] = [
            RelationRow(str(up), self._title(up), -1, current=False)
            for up in ancestors(self._vault, note.oid)
        ]
        rows.append(RelationRow(str(note.oid), note.title or "未命名", 0, current=True))
        rows.extend(
            RelationRow(str(down), self._title(down), 1, current=False)
            for down in descendants(self._vault, note.oid)
        )
        return rows

    def version_rows(self, oid: str) -> list[VersionRow]:
        """历史视图投影：最新在前。"""
        try:
            note = self.note(oid)
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return []
        history = note.history()
        total = len(history)
        return [
            VersionRow(
                total - index,
                str(entry["id"]),
                fmt_time(int(entry["at"])),
                current=index == 0,
            )
            for index, entry in enumerate(history)
        ]

    def _title(self, oid: object) -> str:
        try:
            return self.note(str(oid)).title or "未命名"
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return "（缺失）"

    def group_nodes(self) -> list[GroupNode]:
        """分组导航树投影：有序根组 + 末尾「未分组」笔记。"""
        groups = list(Group.list(self._vault))
        by_gid = {group.gid: group for group in groups}
        contained: set[str] = set()
        for group in groups:
            contained.update(group.group)
        roots = [group for group in groups if group.gid not in contained]
        rank = {gid: index for index, gid in enumerate(self._root_order())}
        roots.sort(key=lambda group: rank.get(group.gid, len(rank)))
        nodes = [self._group_node(group, by_gid, set()) for group in roots]

        referenced = {ref for group in groups for ref in group.group}
        ungrouped: list[GroupNode] = []
        for info in self._vault.iter(type=Note.kind):
            oid = str(info.oid)
            if oid in referenced:
                continue
            node = self._note_node(oid)
            if node is not None:
                ungrouped.append(node)
        if ungrouped:
            nodes.append(GroupNode("group", "", "未分组", tuple(ungrouped)))
        return nodes

    def _group_node(self, group: Group, by_gid: dict[str, Group], seen: set[str]) -> GroupNode:
        children: list[GroupNode] = []
        for ref in group.group:
            if ref in by_gid:
                if ref in seen:
                    continue
                children.append(self._group_node(by_gid[ref], by_gid, {*seen, ref}))
            else:
                node = self._note_node(ref)
                if node is not None:
                    children.append(node)
        return GroupNode("group", group.gid, group.title or "未命名组", tuple(children))

    def _note_node(self, oid: str) -> GroupNode | None:
        try:
            row = NoteRow.from_note(self.note(oid))
        except Exception:  # noqa: BLE001 — 缺失 / 损坏不崩界面
            return None
        return GroupNode(
            "note",
            row.oid,
            row.title,
            updated=row.updated_label,
            preview=row.preview,
        )

    def _root_order(self) -> list[str]:
        raw = self._vault.bucket.catalog.get_meta("group_root_order") or ""
        return [item for item in raw.split(",") if item]

    def _build_rows(self) -> list[NoteRow]:
        infos = sorted(
            self._vault.iter(type=Note.kind),
            key=lambda info: info.updated,
            reverse=True,
        )
        rows: list[NoteRow] = []
        for info in infos:
            try:
                rows.append(NoteRow.from_note(Note.load(self._vault, info.oid)))
            except Exception:  # noqa: BLE001, S112 — 单篇坏数据不拖垮整个列表
                continue
        return rows

    # ---- 变更 ----
    def _on_event(self, event: Event) -> None:
        if not isinstance(event, (ObjectPut, ObjectDeleted)):
            return
        oid = str(event.oid)
        self._rows = None
        self._changed.add(oid)
        self.changed.emit(oid)

    def take_changed(self) -> list[str]:
        """取出并清空自上次以来的变更 oid（供桥接层合并后发信号）。"""
        changed = sorted(self._changed)
        self._changed.clear()
        return changed

    def invalidate(self) -> None:
        """手动作废投影（用于非事件驱动的外部改动）。"""
        self._rows = None
        self.changed.emit("")

    def close(self) -> None:
        """退订内核事件，断开与库的联系。"""
        for subscription in self._subscriptions:
            subscription.cancel()
        self._subscriptions.clear()


__all__ = ["Session"]
