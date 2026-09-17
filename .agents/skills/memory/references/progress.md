<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 进度 / TODO

> 状态：进行中 / 已定 / 已废弃。完成后移入 `changes.md`，或直接删除。
> 细则以 `docs/architecture/*.md` 与代码为准，本文件只记「还没做 + 在做」。

## 进行中

- **M0 底层已落地**（2026-09-17）：正文行身份 + 行内区间样式 + 通用 `VersionStore` + 笔记 Codec；
  下一步往上接 UI 后端 `currentBlocks` 与编辑器本体。

## 待做（近期）

- [ ] **大正文透明分片**：`Note.body` 过大时走 `Bucket.put_content`（分片 + 索引块）。
- [ ] **关系拓扑 UI**：`relations` 表已能查上下游，界面画引用拓扑图未接。
- [ ] **图片 / 音频转码实装**：走不传染库（图片 Pillow；音频 FLAC/Opus），视频按 (a) 暂不转码。
- [ ] 属性 KV 化推广到**项目 / 社区**（现只有笔记是 KV）。
- [ ] 分享目标接真实数据（社区 / 成员现为 demo）。
- [ ] 主题系统「主题文件系统」另行设计（现为单主题令牌）。

## 下阶段（编辑器本体）

- [x] **逐行编辑器首版**（2026-09-17）：`Note` 行级原语 + 后端 `setLineText`/`splitLine`/`mergeLine`/
  `removeLine`/`insertLineAfter`/`toggleLineStyle` + QML 逐行渲染（文本行 / 占位 chip / 行内样式 RichText /
  Ctrl+B/I/U / Enter/Backspace/上下键 / 去抖保存）。**行内样式编辑、光标跨行选区、撤销栈**待迭代。
- [ ] 富编辑增强：跨行选择、撤销/重做栈、样式工具栏（bold/italic/… 之外的颜色/字号）。
- [ ] **编辑器顶部两行工具栏**（Word 式）：文字 / 段落工具几十个，需要先预制样式（color/font/size/对齐等）；
  是富文本编辑器的前置。
- [ ] **笔记列表形态**：详细 / 紧凑 / 分组树 / 锁定 / 口令 / 拖拽移动 / 筛选均已接。
- [ ] 画板绘制：`Graphic`/`Canvas` 的交互与渲染（点路径 + 变换 + 连线走线）。
- [ ] 多媒体拖入：落 `Asset`（转码）→ 正文 `{"access": n}` 占位。
- [ ] 「捕捉面 vs 编辑面」分离落地（全局热键秒开）。

## 远期

- [ ] **Project（重）**：复杂度远高于 note，全部建立在 block / body / bucket 之上。
  - 项目管理 + 类 GitHub 的社区化（issue / PR / 治理）。
  - 多 Action 的兼容与集合。
  - issue / PR 不分开，而是**以即时通信方式组合**的形态。
  - 一套专业 **todo 管理器**：按任务目标性质**自动分析代码、验证 todo 是否真实完成**
    （不是数标签，而是像测试标靶一样验证代码确实满足功能，框架兼 APP 自身）。
  - 前置：先把 note 的底层（body/bucket）打磨稳，project 不再被底层问题牵扯。
- [ ] 任务与进度、应用上下文 / 配置。
- [ ] P2P / 服务端（`src/comm`、`src/server` 实验顶层包）。
- [ ] 真实成员 / 社区发现与信任启动（见 `access.md`）。
- [ ] 正式解锁 / 传输加密流程（本地已不加密）。

## 工程债

- [ ] `src/cairn/ui/theme/`（Widgets + QSS 时代）应用已不引用，仅 `tests/ui/test_theme.py` 在测；待迁移或删除。
- [ ] `src/comm/framing.py` 仍引用 `Block` 时代的字节流；P2P 层待随新模型重做。
- [ ] 包体偏大（onedir 约 206MB）：未剔除未用的 Qt 模块。
- [ ] 可复现构建、代码签名（Authenticode）未做。
- [ ] Linux 服务端 / CLI 入口与 Docker：待 `src/server` 成熟；macOS 暂缓。
