<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 进度 / TODO

> 状态：进行中 / 已定 / 已废弃。完成后移入 `changes.md`，或直接删除。
> 细则以 `docs/architecture/*.md` 与代码为准，本文件只记「还没做 + 在做」。

## 进行中

- UI 外壳打样：`Shell` / `EditorArea` / `RightDock` / `NoteMenu` / `SharePopover` 已成型；基板富编辑落地后再补命令带的「文字修改行」。
- 把根 `AGENTS.md` 的长规则逐步迁入 `rules/references/`，根文件只留索引。
- 评估并安装其它 skill（UI / memory 相关，skills.sh）。

## 待做（近期 · 周边）

- [ ] 属性 KV 化推广到**项目 / 社区**（现只有笔记是 KV；两者仍是静态示例）。
- [ ] 标签 `K:V` **父子关系推导** + **基于标签搜索**（现只存 `K:V` 字符串，未用）。
- [ ] 分享目标接真实数据（社区 / 成员现为 demo；「分享对象不在本机档案时」已有分享项不显示）。
- [ ] 历史页（版本）体验复核。
- [ ] 主题替换：需要一套「主题系统文件系统」，另行设计。

## 下阶段（编辑器本体）

- [ ] 基板富编辑 / 多媒体：块编辑、画布、矢量、嵌入（见 `note-model.md` §6 / §9）。
- [ ] 「捕捉面 vs 编辑面」分离落地（全局热键秒开）。

## 远期

- [ ] 多空间 UI；正式解锁流程（现为开发固定口令）。
- [ ] 任务与进度、应用上下文 / 配置（见 `kernel.md` 预留节）。
- [ ] P2P / 服务端（`src/comm`、`src/server` 实验顶层包）。
- [ ] 真实成员 / 社区发现与信任启动（见 `access.md`）。

## 工程债

- [ ] `src/cairn/ui/theme/`（Widgets + QSS 时代）应用已不引用，仅 `tests/ui/test_theme.py` 在测；待迁移为 QML 令牌或删除。
- [ ] `rules` / `memory` 自建骨架「备注待补」。
- [ ] 包体偏大（onedir 约 206MB）：未剔除 `Qt6Widgets` / Quick3D / Graphs 等未用模块。
- [ ] 可复现构建（为日后代码签名留后路；签名后不可再改文件）。
- [ ] 代码签名（Authenticode）未做；当前产物会被 SmartScreen 拦。
- [ ] Linux 服务端 / CLI 入口与 Docker：待 `src/server` 成熟再做；macOS 暂缓。

## 数据结构（`data-model.md` 待落地）

- [ ] **基板升格**为公共底座；`note` 降为角色；建 `type → format` 映射表。
- [ ] **阈值溢出**（内联 ↔ 独立叶）+ 滞回；`shape` / `group` 片段。
- [ ] **物理打包**（追加 pack + 索引 + 压实）；**加密前压缩**。
- [ ] **表示升级**（单叶 ↔ 基板树 / rope，"big note"＝rope 根）。
- [ ] **可视区惰性加载** + 叶 LRU 缓存。
