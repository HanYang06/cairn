# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""笔记的版本 Codec：**按行 id 锚定**的反向补丁，交给通用 ``VersionStore``。

一次变更 = 一个补丁（新 → 旧，供反向回放）：

    {"<行id>": {"act": "PUT",  "v": 旧内容, "style": 旧样式, "after": 前驱行id|null}}
    {"<行id>": {"act": "DROP"}}
    {"@order": [旧顺序的行 id, ...]}                       # 仅顺序变了才出现

- 未变更的行不进补丁；顺序变化只记 ``@order``。
- ``PUT`` 的载荷是**旧值**（回放时写回去）；``DROP`` 表示该行是较新版新增的。
- 行 id 是稳定锚点，所以行增删 / 重排不会让既有补丁失效。
"""

from __future__ import annotations

from typing import Any

from blake3 import blake3

from core.storage import canonical
from core.types import type_name

from .edit.body import is_marker
from .model import NOTE_KIND

State = dict[str, Any]  # {"body": [{"id","v"}], "style": {lid: [[s, e, data], ...]}}


def digest(state: State) -> str:
    """内容签名（丢行 id）：同文同样式即同签名。"""
    view: list[list[Any]] = []
    style = state.get("style") or {}
    for line in state.get("body") or ():
        if is_marker(line["v"]):
            view.append([])
            continue
        view.append([list(item) for item in (style.get(line["id"]) or ())])
    payload = {
        "type": type_name(NOTE_KIND),
        "body": [line["v"] for line in state.get("body") or ()],
        "para": [line.get("p") or {} for line in state.get("body") or ()],
        "style": view,
    }
    return blake3(canonical(payload)).hexdigest()


def diff(new_state: State, old_state: State) -> bytes:  # noqa: C901 — 三趟 diff 逻辑集中
    """算出把 ``new`` 回退成 ``old`` 的补丁。"""
    new_by = {line["id"]: line for line in new_state.get("body") or ()}
    old_by = {line["id"]: line for line in old_state.get("body") or ()}
    new_style = new_state.get("style") or {}
    old_style = old_state.get("style") or {}
    old_order = [line["id"] for line in old_state.get("body") or ()]

    patch: dict[str, Any] = {}

    for lid in new_by:
        if lid not in old_by:
            patch[lid] = {"act": "DROP"}

    for index, lid in enumerate(old_order):
        if lid in new_by:
            continue
        entry: dict[str, Any] = {"act": "PUT", "v": old_by[lid]["v"]}
        if old_by[lid].get("p"):
            entry["p"] = old_by[lid]["p"]
        if lid in old_style:
            entry["style"] = old_style[lid]
        entry["after"] = old_order[index - 1] if index > 0 else None
        patch[lid] = entry

    for lid, old_line in old_by.items():
        new_line = new_by.get(lid)
        if new_line is None:
            continue
        if (
            old_line["v"] != new_line["v"]
            or old_line.get("p") != new_line.get("p")
            or old_style.get(lid) != new_style.get(lid)
        ):
            entry = {"act": "PUT", "v": old_line["v"]}
            if old_line.get("p"):
                entry["p"] = old_line["p"]
            if lid in old_style:
                entry["style"] = old_style[lid]
            patch[lid] = entry

    new_common = [line["id"] for line in new_state.get("body") or () if line["id"] in old_by]
    old_common = [lid for lid in old_order if lid in new_by]
    if new_common != old_common:
        patch["@order"] = old_order

    return canonical(patch) if patch else b""


def apply(state: State, patch: Any) -> State:  # noqa: C901 — 反向回放：三类动作集中
    """把反向补丁作用到状态上，得到旧状态。"""
    body = [dict(line) for line in state.get("body") or ()]
    style = {
        lid: [list(item) for item in triples] for lid, triples in (state.get("style") or {}).items()
    }

    for lid, entry in patch.items():
        if lid == "@order":
            continue
        if entry.get("act") == "DROP":
            body = [line for line in body if line["id"] != lid]
            style.pop(lid, None)

    for lid, entry in patch.items():
        if lid == "@order" or entry.get("act") != "PUT":
            continue
        record = {"id": lid, "v": entry["v"]}
        if entry.get("p"):
            record["p"] = entry["p"]
        found = next((index for index, line in enumerate(body) if line["id"] == lid), -1)
        if found >= 0:
            body[found] = record
        else:
            after = entry.get("after")
            position = 0
            if after:
                index = next((i for i, line in enumerate(body) if line["id"] == after), -1)
                position = index + 1 if index >= 0 else 0
            body.insert(position, record)
        if "style" in entry:
            style[lid] = entry["style"]
        else:
            style.pop(lid, None)

    if "@order" in patch:
        rank = {lid: index for index, lid in enumerate(patch["@order"])}
        body.sort(key=lambda line: rank.get(line["id"], len(rank)))

    return {"body": body, "style": style}


class NoteCodec:
    """笔记版本 Codec：实现 ``VersionStore`` 需要的三件事。"""

    def digest(self, state: State) -> str:
        return digest(state)

    def diff(self, new_state: State, old_state: State) -> bytes:
        return diff(new_state, old_state)

    def apply(self, state: State, patch: Any) -> State:
        return apply(state, patch)


NOTE_CODEC = NoteCodec()

__all__ = ["NOTE_CODEC", "NoteCodec", "State", "apply", "diff", "digest"]
