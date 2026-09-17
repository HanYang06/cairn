<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 进度 / TODO

> 状态：进行中 / 已定 / 已废弃。完成后移入 `changes.md`，或直接删除。
> 细则以 `docs/architecture/*.md` 与代码为准，本文件只记「还没做 + 在做」。

## 进行中

- **编辑器本体-工具线**（2026-09-17）：工具四分类 + 只读状态 + 工具栏三态高亮已落地；
  下一步拆 `添加型` 的底层（表格 / 画板 / 多媒体）与 `查询型`（查找替换）实现。

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
  Ctrl+B/I/U / Enter/Backspace/上下键 / 去抖保存）。
- [x] **格式工具栏（两行）**（2026-09-17）：`domains/note/tools.py` 预设两行编辑型；溢出向下抽屉。
- [x] **工具本体四分类**（2026-09-17）：`ToolCategory`（添加 / 编辑 / 命令 / 查询）；`Tool.state` 只读三态 +
  `Backend.toolState`；工具栏按钮高亮（生效 / 未生效 / 混合）；命令型（收藏/归档/复刻/关系/历史/分享/属性）
  纳入工具体系、去掉单独动作行；添加型 `insert-code` 实装。详见 `changes.md`。
- [ ] **跨行选区 + 拖拽出视窗自动滚动**（下一优先）：现受「1 硬行 = 1 个 TextEdit」限制，仅能行内选；
  人类已被 Office 养刁，属必备项；需改编辑模型（文档级选区）。
- [ ] **撤销 / 重做栈**：逐行编辑尚无 undo/redo。
- [ ] **添加型底层**：表格数据模型；画板交互与渲染；多媒体文件选择 / 转码入正文。
- [ ] **查询型（查找替换）**：已登记 `find` / `replace`（`available=False`）框架，面板与匹配逻辑未写；
  进阶考虑按语法替换 / 选择替换 / 高级替换。
- [ ] **拖拽自定义布局**：工具「分组与位置是数据」，UI 重排 + 持久化文件未做；前置=工具先整理好。
- [ ] **笔记列表形态**：详细 / 紧凑 / 分组树 / 锁定 / 口令 / 拖拽移动 / 筛选均已接。
- [ ] 画板绘制：`Graphic`/`Canvas` 的交互与渲染（点路径 + 变换 + 连线走线）。
- [ ] 多媒体拖入：落 `Asset`（转码）→ 正文 `{"access": n}` 占位。
- [ ] 「捕捉面 vs 编辑面」分离落地（全局热键秒开）。

## UI 重建（Widgets 宿主 + QML 岛，2026-09-18）

> 方向见 `decisions.md`；规则见 `rules/references/ui-boundary.md`。现有 QML 逐块迁到 Widgets。

- [x] **P0 骨架**（2026-09-18）：`App` 组合根 + `MainWindow/Shell` + `Component/Panel/Page` 基类
  + 主题令牌统一为 GitHub 色板（`ui/theme` 单一真源）+ `--widgets` 入口 + 离屏冒烟。
- [x] **组件层起步**（2026-09-18）：`Component` 继承注册表 + `STYLABLE` / `STATES`
  （抽象基类不入册）；原子 `Label` / `Button` / `IconButton` / `Field` / `Section`；
  `theme/schema.py` 由注册表自动派生点分路径 + `validate_path`。
- [ ] **P1 导航 + 检查器**：`Session`（身份缓存 + 投影）+ 类型化行 + `QTreeView/QListView` 模型 +
  `Inspector`（`QFormLayout` 或属性模型）。
- [ ] **P2 编辑器**：`QTextEdit`/`QTextDocument`（block ↔ 行映射）+ `QUndoStack`；
  替换 QML 逐行 `TextEdit`；解决跨行选区与撤销/重做。
- [ ] **P3 视图与对话框**：关系 / 历史页，菜单 / 弹层 / 命令面板。
- [ ] **P4 QML 岛**：画板、关系拓扑等按边界规则接入。
- [ ] 删除 QML 主界面与 `ui/theme` 旧暖色令牌；同步/生成 `CairnTheme.qml`（若仍留 QML 岛）。

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

- [ ] `src/comm/framing.py` 仍引用 `Block` 时代的字节流；P2P 层待随新模型重做。
- [ ] 包体偏大（onedir 约 206MB）：未剔除未用的 Qt 模块。
- [ ] 可复现构建、代码签名（Authenticode）未做。
- [ ] Linux 服务端 / CLI 入口与 Docker：待 `src/server` 成熟；macOS 暂缓。

### 内核小账（2026-09-18 复核，非欠账，是收口）

- [ ] **props 双存储**：`Note` 有类型化 `favorite/archived/trashed/privacy` 字段
  （`note/types.py`），但 UI 全程读写 `attrs["props"]`（`backend.py`）→ 类型字段实际是死的。二选一收口。
- [ ] **`Vault` 死 API**：`put` / `put_meta` / `versions` / `read_version` / `restore_version`
  （旧单版本占位）与 `VersionStore` 并存，误导人。清理或明确标注废弃。
- [ ] **`Vault.put_block` 不发 `ObjectPut`**：领域 `save()` 走它，导致 UI 收不到内核变更事件；
  补发以建立单一变更通路（`events.py` 已声明「提交后发出」）。
- [ ] **pack 压实**：`gc` 空实现、`compact` 只压版本；事务回滚会留孤儿 pack 字节。需压实/回收策略。
