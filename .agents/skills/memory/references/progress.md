<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 进度 / TODO

> 状态：进行中 / 已定 / 已废弃。完成后移入 `changes.md`，或直接删除。
> 细则以 `docs/architecture/*.md` 与代码为准，本文件只记「还没做 + 在做」。

## 进行中

- 笔记底层已整体落地（存储桶/块、领域继承、关系 DB、版本 diff），正往编辑器本体与 UI 接。

## 待做（近期）

- [ ] **大正文透明分片**：`Note.body` 过大时走 `Bucket.put_content`（分片 + 索引块）。
- [ ] **文档回写**：`docs/architecture/storage.md`、`data-model.md` 仍是旧的加密/双源模型，需按桶/块重写。
- [ ] **关系拓扑 UI**：`relations` 表已能查上下游，界面画引用拓扑图未接。
- [ ] **图片 / 音频转码实装**：走不传染库（图片 Pillow；音频 FLAC/Opus），视频按 (a) 暂不转码。
- [ ] 属性 KV 化推广到**项目 / 社区**（现只有笔记是 KV）。
- [ ] 分享目标接真实数据（社区 / 成员现为 demo）。
- [ ] 主题系统「主题文件系统」另行设计（现为单主题令牌）。

## 下阶段（编辑器本体）

- [ ] 富编辑：正文块编辑、样式拆合、光标/选区（`note/edit.py` 已备文本编辑原语）。
- [ ] 画板绘制：`Graphic`/`Canvas` 的交互与渲染（点路径 + 变换 + 连线走线）。
- [ ] 多媒体拖入：落 `Asset`（转码）→ 正文 `{"access": n}` 占位。
- [ ] 「捕捉面 vs 编辑面」分离落地（全局热键秒开）。

## 远期

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
