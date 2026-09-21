<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 变更

- 2026-09-14 · 已定 · 建立规则 / 记忆机制，新增 `rules`、`memory` 技能与 `.agents/skills/` 约定 | 见 `AGENTS.md`
- 2026-09-14 · 已定 · 安装 `skill-creator`（`anthropics/skills`，Apache-2.0）与 `git-commit`（`github/awesome-copilot`，MIT） | skills.sh CLI
- 2026-09-14 · 已定 · 修复热重载：`HotReloader` 原被 GC（watcher 失效）+ 重载脆弱；改为绑定 `Loader.source` 到带版本号的 URL，保留引用并挂到 engine | 见 `ui/app.py`
- 2026-09-14 · 已定 · UI 大改：布局契约（SplitView/折叠/聚焦）、笔记页命令带、右键菜单、分享弹层、回收站、KV 属性、标签 KV 编辑、触发条移入标题栏 | 见 `ui-theme.md` §7
- 2026-09-14 · 已定 · 内核新增 `Vault.put_meta` + `Index.update_meta`：元数据更新不产生版本；`Note.update` 仅内容变化才版本化 | 见 `note-model.md` §4.1
- 2026-09-14 · 已定 · README 扩写并修正：Qt Widgets→Qt Quick/QML，补现状 / 快速开始 / 架构 / 平台分发规划 | 见 `README.md`
- 2026-09-14 · 已定 · `ui-theme.md` 按 QML 现状修正 §1–§6：QSS/Widgets 表述改 QML 令牌，QtWebEngine 标为预留 | 见 `ui-theme.md`
- 2026-09-14 · 已定 · Windows 打包闭环：`packaging/cairn.spec`（PyInstaller onedir，显式带 QML、剔除 WebEngine）+ `packaging/windows/cairn.iss`（Inno）+ `tools/build.py` + CI；产物 206MB，`--smoke` 通过 | 见 `tools/build.py`
- 2026-09-14 · 已定 · 新增 `src/cairn/__main__.py`：`python -m cairn` 与冻结入口 | —
- 2026-09-14 · 已定 · 多选 + 批量（标签/收藏/回收）、关系图信息增强（作者/时间/因果）、无障碍（reduceMotion / highContrast）、`ObjectInfo` / `VersionInfo` 加 `author` | 见 `ui-theme.md` §7.6–7.8
- 2026-09-14 · 已定 · 笔记页去「快速记录」只留搜索、空白双击新建；左栏悬停去过渡（修双高亮）；工具册修复 `triggerHover` 悬空引用 + 延时回收 + 点外即收；关系图重做为竖排 Git 式泳道 | 见 `ui-theme.md` §7.8–7.10
- 2026-09-14 · 已定 · 新增 `docs/architecture/data-model.md`：数据结构总纲；`storage.md`/`note-model.md`/`AGENTS.md` 加指针 | 见 `data-model.md`
- 2026-09-15 · 已定 · 数据模型大改（平行分布存储 / 结构进 DB / 画板 / 正文块列表） | 决策见 `decisions.md` 2026-09-15
- 2026-09-16 · 已定 · **存储层重写**：新增 `core/store`（Bucket/Block/Catalog/Table）；`Vault` 降为应用门面；
  删除 `core/storage/*` 与 `core/crypto.py`（加密/清单/空间/分块池）。落盘格式不兼容。
- 2026-09-16 · 已定 · 领域全部**直接继承 `Block`**；note 结构迁入 `note/types.py`（body=list、style 对齐、
  `Canvas`/`Graphic`/`Paint`/`Access`）；`Attr(item=)` 类型化列表。
- 2026-09-16 · 已定 · 外置图形集 `config/shapes.json` + `note/shapes.py`；标签改 dict；新增 `author`/`authors`；
  `Asset` 入库先转码（草案，恒等）。
- 2026-09-16 · 已定 · 关系落 DB（`relations` 表，多类型）；`composition` 并入 note。
- 2026-09-16 · 已定 · 笔记版本：增量 diff 落 DB（`note/versions.py` + `versions` 表），30 天惰性压实；
  历史面板接真实版本。
- 2026-09-16 · 已定 · UI 主题换 GitHub 色盘 + 等宽字体链 + 苹果式圆角/柔和阴影。
- 2026-09-17 · 已定 · **M0 底层编辑/版本模型**：`note/model.py`（纯数据）/`edit.py`（行身份+区间样式）/`types.py`
  （Note 新 body/style、id-free cID）；新增通用 `core/store/version.py`（`VersionStore`，prev 链 + 反向补丁）；
  `note/versions.py` 改为笔记 `Codec`；`Block.decode` 改用子类 `compute_checksum`。旧 `normalize/bare/blank_styles`
  与平行 style list 移除。ruff/mypy/pytest 全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **body 内容池 + 去重口径**：`checksum = body_hash`（只算 body，剥离行 id），
  `contents` 成为桶内去重池（O(1)）；`attrs` 拆出随块行存（`blocks.meta`）；`Attr`/`Body` 泛型化；
  `note.body` 变 `BodyLines`（带 `.hash`）。回退 nid/pid。ruff/mypy/137 测试全绿。
- 2026-09-17 · 已定 · **Body 基类化**：核心 `Body` 改为容器基类（`hash` 状态字段 + `content()` + `refresh()`），
  旧描述符改名 `BodyField`；`NoteBody(Body)` = `text` + `style`，`content()` 剥行 id；`Note.body: NoteBody = NoteBody()`
  类型自证、自动每实例一份；`note.style` 代理 `body.style`。ruff/mypy/140 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **字段/内容类型归一**：`Attr`=属性、`Data`=数据（裸容器注解自证、免标记）；
  `Canvas` 升格为块 `cairn.canvas`（`CanvasBody`），note 存 canvas oid；**去掉 `Access`**（并入 `Asset`），
  note 存 asset oid。`domains/{canvas,asset}.py`。ruff/mypy/140 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **字段系统 + 强签名 + Block 瘦身**：`Attr` 加 `coerce` 与单值类型化；
  新增 `domains/signature.py`（复合签名：alg/author/created/subject/prev/value，自校验）；`Note.signature`
  为类型化字段，创建时锁创作签名；`title/tags/authors` 从 `Block` 移到 Note/Project/Asset；删除
  `note.derived`、`note.share` 旧字段；`body: Body[NoteBody] = NoteBodyField()` 声明。
  ruff/mypy/140 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **质量门禁升级到企业级-ε**：mypy 开 `strict`（`src`+`tools`，`Attr` 插件已兼容）；
  ruff 改 `select=["ALL"]` + 精选 ignore + `ruff format`；pytest 加 `--strict-markers/--strict-config`、
  `filterwarnings=error`、覆盖率行+分支 ≥80%（CI 门禁）；新增 `.pre-commit-config.yaml`（ruff→mypy）与
  `.github/workflows/ci.yml`；dev 依赖加 `pytest-cov`/`pre-commit`。修掉 79 条 sqlite 未关闭连接告警
  （`Catalog.__del__` 兜底释放句柄）。标准写入 `rules/references/quality.md`。ruff/format/mypy/140 测试全绿。
- 2026-09-17 · 已定 · **旧概念残留清理**：删 `Space`/`SpaceId`/`Visibility`/`SpaceNotFoundError`/`VaultLockedError`、
  `VaultUnlocked`/`VaultLocked`/`SpaceCreated` 事件、`ChunkRef`、`VerifyReport.chunks`、`ObjectInfo.space_id`、
  `_PoolShim`、`Vault.space()`/`put(space=)`/`iter(space=)`、`Relation`/`provenance` 的 `space` 参数、
  `Block.space_id`、`domains/types/substrate.py`（旧「基板」）与 `_SPACE_LABELS`；
  backend 空间标签改 `currentVaultLabel`（TitleBar / 属性面板同步）。ruff/mypy/137 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **文档回写**：`domains.md` 整篇重写（`Block` 基类 + `Attr`/`Data`/`Body` + 业务表 + 关系表）；
  `data-model.md` 重写为 v0.4（桶 / 块 / 内容池 / 目录 / 通用版本引擎）；`note-model.md` 修 §2/§3/§9/§10；
  `kernel.md`（事件目录 / 配置）、`access.md`、`network.md`、`ecosystem.md`、`README.md`、`AGENTS.md` 同步；
  `ui-theme.md` 色板 / 字体 / 圆角更新为 QML 现状（GitHub Primer + 等宽字体链）。
- 2026-09-17 · 已定 · **逐行编辑器首版**：`note/edit.py` 新增行级原语（改字/插入/删除/拆分/合并 + 区间样式切换，
  拆合时样式按位置迁移）；`Note` 暴露 `set_line`/`insert_line_after`/`remove_line`/`split_line`/`merge_line`/`toggle_style`；
  `Backend` 加行级 Slot 与 `_touch` 去抖保存；`EditorArea.qml` 正文由单一 `TextEdit` 改为消费 `currentBlocks`
  的逐行编辑器（RichText 行内样式、占位 chip、Ctrl+B/I/U、Enter/Backspace/上下键）。ruff/mypy/151 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **保存 ≠ 版本**：`Note` 拆出 `persist()`（只落盘）与 `save()`（落盘 + 版本检查点）；
  自动保存走 `persist`，检查点在四类「非连续编辑」边界产生——空闲 `CHECKPOINT_IDLE_MS`（默认 5 分钟）、
  切换笔记、`Ctrl+S`（`Backend.saveNow`）、退出（`Backend.shutdown` ← `aboutToQuit`）。
  修掉逐次自动保存堆出一长串微小版本的问题。ruff/mypy/153 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **快赢三件套**：① 工具册点击回收修好（`backdrop` 仅在点面板外时关闭）；
  ② 属性栏补 `署名` / `签名` / `可见性`，并把 `作者` 改取笔记 `author`（原误用当前档案名）；
  ③ 去掉笔记侧栏搜索框，工具册输入框升级为搜索 / 命令面板（`Backend.searchNotes`：输入即筛、
  回车打开首条、无结果以该文本新建、Esc 清空、关闭复位过滤）。ruff/mypy/154 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **新增组块 `cairn.group`**（`domains/group.py`）：域身份 **`gid`**（≠ 块 `oid`）；
  `group: list[str]` 有序子项（组存 gid、其余存 oid，可无限嵌套）；`title` / `lock` / `owner` / `member` / `key`
  （社区化预埋；`User` 系统落地前用字符串）；成员**两套都存**（列表存结构 + `relations` 存 `contains` 反查）。
  导航树未接。ruff/mypy/160 测试全绿。
- 2026-09-17 · 已定 · **后端组 API + 导航分组树**：`Backend` 加 `groupTree` / `groupChoices` /
  `createGroup` / `renameGroup` / `toggleGroupLock` / `setGroupKey` / `deleteGroup` / `addNoteToGroup` /
  `removeNoteFromGroup`；`Navigator` 笔记区改为**分组树**（组可折叠、双击改名、悬停＋当前笔记；
  无组时平铺 + 「未分组」兜底），并加**详细 / 紧凑**显示形态切换。ruff/mypy/164 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **组功能补全**：锁定（锁后改名/删除/增删/移动一律拒绝）、口令（`key` 存 BLAKE3 校验哈希，
  `unlockGroup` 解锁当前会话；未解锁不暴露子项）、移动/重排（`moveGroup` 防环、`reorderGroup` 含根序、
  `reorderInGroup`）、筛选（`filterByGroup` / `clearGroupFilter` / `groupFilter`）、`clearNoteGroups`（拖回未分组）。
  UI：`GroupMenu.qml` 组右键菜单、`PromptBox.qml` 口令输入、`Navigator` 拖拽（笔记/组拖到组上增删与移动）。
  ruff/mypy/170 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **行级（段落）属性 `p` + 超长行**：行元素变 `{id, v, p?}`（`p` 放 align/heading/list/level/block）；
  `NoteBody.content`/hash、`NOTE_CODEC`(digest/diff/apply)、`Note._state`、`Note.blocks` 一并纳入；
  新增 `Note.set_paragraph`/`clear_paragraph` 与后端 `setParagraph`/`clearParagraph`。
  约定 **1 硬行 = 1 段**（不设独立段落实体）。另加 `text_weight` / `OVERLONG_WEIGHT(300)` 与 `overlong` 标志；
  编辑器超长行 `NoWrap` + 横向滚动 + 右下「到行末」按钮。ruff/mypy/178 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **格式工具栏（两行）+ 域工具 + 行内 set/clear**：`domains/note/tools.py`（`Tool` 基类 +
  参数化实例、`TOOLS` 注册表、`PRESET_LAYOUT`）；`edit.py` 加 `set_range_style` / `clear_range_style` / `style_at`，
  `Note.set_style_span` / `clear_style_span`；后端 `tools` / `toolLayout` / `runTool`；
  `FormatToolbar.qml`（字级行 + 段级行、纯图标 + `Tips`、溢出**向下抽屉**）；`EditorArea` 段落渲染
  （对齐 / 标题字号字重 / 列表序号派生 / 缩进 / 引用左条 / 代码块等宽底色 `NoWrap`）。
  导航去掉「全部笔记」标签；标题栏最大化/还原图标随 `Window.visibility` 切换。
  ruff/mypy/188 测试全绿，`--smoke` 通过。
- 2026-09-17 · 已定 · **工具本体四分类 + 当前态高亮**：`tools.py` 加 `ToolCategory`（add/edit/command/query）、
  `Tool.available` 与只读 `Tool.state`（`bool|None` 三态），编辑型全部补 `state`；新增添加型 `insert-code`
  与预留 `insert-table`/`insert-canvas`/`insert-access`；`edit.py` 加 `bool_state`；新增 `ui/tools.py`
  （命令型 + 查询型 `find`/`replace` 元数据，命令行为由 UI 回调 `Backend`）；`Backend.tools` 合并四类，
  新增 `toolState` / `toolGroups`，`runTool` 返回聚焦行 id；`FormatToolbar` 三态高亮 + `toolTriggered(tid, source)`，
  抽屉按类别分组，修掉按钮底色不恢复的问题；`EditorArea` 去掉单独动作行、命令并入工具体系。
  ruff/mypy/195 测试全绿（覆盖率 83%），`--smoke` 通过。
- 2026-09-18 · 已定 · **UI 路线转 Widgets 宿主 + QML 岛，P0 骨架落地**：`App` 组合根（`ui/root.py`）、
  `MainWindow`/`Shell`（`ui/window.py`）、`Component`/`Panel`/`Page` 基类（`ui/components/base.py`）；
  主题令牌统一为 GitHub 色板并成单一真源（`ui/theme/` + `current_theme` 状态），QSS 全应用一次；
  `cairn --widgets` 入口（QML 路径不变）；`ObjectPut` 事件补进 `progress.md` 待办。
  测试：`tests/ui/conftest.py`（会话级离屏 `QApplication`）、`test_widgets.py`、`test_widgets_smoke.py`；
  `test_backend.py` 的 `QCoreApplication` 改 `QApplication`（Qt 单实例）。ruff/mypy/202 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **UI 状态直通地基**：`Vault.put_block` 补发 `ObjectPut`（新增 `checksum` 字段，
  事件在写入后发出）；新增 `ui/signal.py`（Qt-free `Signal`/`Subscription`/`Cancellable`）、
  `ui/format.py`（`fmt_time`/`fmt_size`，backend 复用去重）、`ui/rows.py`（`NoteRow` 类型化投影）、
  `ui/session.py`（`Session`：投影缓存 + 变更信号，Qt-free）、`ui/bridge.py`（`SessionBridge`：
  合并成 Qt 信号）、`ui/models.py`（泛型 `ListModel[T]`）；`Component.watch` 生命周期安全订阅；
  `App` 组合根挂 `session`/`bridge`。链路：内核 → Session → Bridge → Model，单向。
  ruff/mypy/214 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **布局原语**：`ui/components/layout.py`（`Box`/`VBox`/`HBox`/`Grid`/`Split`），
  纯几何、组合优先；`Shell` 改用 `VBox` + `Split`（上层代码变简单）。设计四规则入
  `rules/references/ui-boundary.md` §6 与 `decisions.md`。ruff/mypy/219 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **组件层 + 主题 schema**：`Component` 加继承注册表（`__init_subclass__`；
  抽象基类 `abstract=True` 不入册，`Box`/`Page` 已标）+ `STYLABLE`/`STATES` 声明；新增原子
  `Label`/`Button`/`IconButton`/`Field`/`Section`；`theme/schema.py` 由注册表 + `Theme` 字段
  自动派生点分路径（`token.*` / `widget.<类型>[.<状态>].<属性>` / `main`）并提供 `validate_path`。
  ruff/mypy/228 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **主题包文件系统**：`config/theme/*.json`（**文件名即主题名**）两段式
  （全局 `token` 块 + `style` 块，**CSS 式选择器 → 声明块**：`"widget.Button:hover": {…}`）；
  `theme/loader.py` 目录扫描 + 加载 + schema 校验（未知段/选择器/属性报错）；`theme/qss.py` 编译
  （令牌 QSS + 部件规则，选择器 `QWidget[cairnClass=…]`）；`theme/schema.py` 导出 `json_schema()`
  （`style.propertyNames` 枚举合法选择器），落 `schema/theme.json`（生成器 `tools/gen_theme_schema.py`，
  测试防漂移）；内置 `github-light` / `github-dark`；`ThemeManager.apply_default()`。
  注册表限 `cairn.ui.components` 下，词汇表确定。ruff/mypy/235 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **结构件起步 + Stack**：`components/layout.py` 加 `Stack`（`QStackedWidget`，
  页面/视图切换）；新增 `components/structure.py`（`Toolbar`：图标动作 + `triggered(id)` 意图）；
  `components/__init__` 导出。规则补「组合可递归，类型仍为组合类型」。schema 自动含新部件。
  ruff/mypy/238 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **原子补齐 + 可样式化载体**：`Component` 开 `WA_StyledBackground`（纯 QWidget
  子类也能被 QSS 背景命中）；原子加 `Divider` / `Chip` / `ToggleSwitch`；schema 自动含新部件。
  ruff/mypy/241 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **组合层起步**：`components/structure.py` 加 `ListPanel`（标题 + `Toolbar` +
  `QListView`；行激活发 `activated(key)`，数据来自 `ListModel`）；组合可递归（结构件可再嵌结构件）。
  ruff/mypy/242 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **App 共享模型 + Shell 接真实列表**：`App` 建 `ListModel[NoteRow]`，
  桥变更自动刷新（`reload_notes`），并暴露 `note_title`；`Shell` 导航改用 `ListPanel` 绑 `app.notes`，
  行激活显示标题（编辑器 / 检查器仍占位）。ruff/mypy/244 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **主页面骨架**：新增 `ActivityBar`（竖向条目 + `activated(id)`）；`Shell` 改 `HBox`
  （活动栏 + Split），中央用 `Stack` 做页面路由（笔记 / 项目 / 社区占位）；导航行激活切回笔记页。
  ruff/mypy/245 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **检查器结构件 + 当前笔记联动**：`PropertyRow` 类型化行；`Session.note_properties`
  投影属性（类型/库/作者/签名/标签/收藏/归档/创建/修改/字数/大小）；`App` 记当前笔记、维护
  `properties` 模型（`current_changed` / `properties_changed`）；`InspectorPanel` 结构件接属性模型；
  `Shell` 导航激活 → `App.open_note`。ruff/mypy/247 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **动画封装 + QML 承载器 + Widgets 预览**：`ui/motion.py`（`animate`/`fade`/
  `make_animation`，时长/缓动走主题令牌，`reduce_motion` 降为 0）；主题加动效令牌；
  `ui/qmlhost.py`（`QmlView` 包 `QQuickWidget`，注入上下文）；`tools/preview_widgets.py`
  离屏/原生渲染外壳为 PNG。修字体：QSS 不再写死 `font-family`（交回应用级回退链），
  `IconButton` 用图标字体，字体链补中文字体兜底。ruff/mypy/251 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **富文本编辑器控件**：`ui/editor/`——`formats.py`（扩展点：段落属性整块存
  `PARA_MAP` 用户属性、行内 `Style` ↔ `QTextCharFormat`、嵌入占位存 kind/index）、`document.py`
  （`NoteDocument`：1 行 = 1 block、行 id 存用户属性、`load_note`/`to_body` 双向无损）、`editor.py`
  （`NoteEditor`：`body_changed` 意图 + 原生 undo/redo/跨行选区）。内核加 `Note.set_body`；
  `App` 去抖落盘 + 切换/退出 flush；`Shell` 笔记页接编辑器。ruff/mypy/254 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **UI 目录重组（分层归位）**：`Component` 提到 `ui/component.py`（中性位置，
  解「布局 ↔ 组件」循环）；布局原语移 `ui/layout/`（**纯几何组织器**，不再入主题词汇表）；
  `Page` 移 `ui/pages/`（页面层独立扩展）；编辑器并入 `ui/components/editor/`（它算组件）。
  schema 随之只含组件（无 VBox/Stack 等布局）。ruff/mypy/254 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **命令注册表 + UI 设置存储**：命令在 `ui/commands.py` 内存声明（id/标题/行为 +
  快捷键/分组/enabled/check，快捷键可被设置覆盖），`ui/default_commands.py` 一处声明内置命令；
  `ui/settings.py` 点分键 JSON 设置（`<root>/.cairn/ui.json`）——**非领域偏好，独立文件，不进 bucket**；
  `App` 持 `settings`/`commands` + `run_command`/`create_note`；`Shell` 改监听 `current_changed`
  载入编辑器（单一通路）。ruff/mypy/263 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **主题增强（elevation + 有限 transition）**：主题加阴影令牌
  （`shadow_color/blur/offset`）；`ui/effects.py` 用 `QGraphicsDropShadowEffect` 施加阴影；
  主题 `style` 里 `widget.<类型>.elevation` 是**声明**，`build_elevations` 编译成「类名 → 层级」，
  `ThemeManager` 存入主题状态，`Component.showEvent` 首次显示时自动施加——QSS 仍不写 elevation，
  效果走代码。`motion.transition`：信号触发属性动画。ruff/mypy/269 测试全绿（覆盖率 84%）。
- 2026-09-18 · 已定 · **迁移①地基：分组树投影 + 通用 TreeModel**：`rows.GroupNode`（组可嵌套 /
  笔记叶子）；`Session.group_nodes()`（按 `group_root_order` 排序根组 + 末尾「未分组」笔记）；
  `models.TreeModel[T]`（按 `children_of` 展开的 QAbstractItemModel，QTreeView 可直接绑）。
  ruff/mypy/272 测试全绿（覆盖率 84%）。迁移顺序：① 分组树 → ② 关系/历史 → ③ 工具栏/命令 →
  ④ 菜单/工具册/弹层 → ⑤ 切默认删 QML。
- 2026-09-18 · 已定 · **迁移① Navigator 分组树**：新增 `components/navigator.py`（`NavigatorPanel`：
  标题 + 工具条 + `QTreeView` + 右键意图）；`App` 加 `groups: TreeModel[GroupNode]` 与分组操作
  （create/rename/delete/toggle_lock/add_note/remove_note/move/clear_note_groups/trash_note），
  桥变更自动刷新；`Shell` 导航换成分组树、右键菜单接操作；`layout.Box.align` + ActivityBar 固定尺寸
  修「子件被摊开」。ruff/mypy/273 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **迁移②：标签页 + 关系 / 历史视图**：`rows` 加 `RelationRow` / `VersionRow` /
  `TabRow`；`Session.relation_rows`（上下游）/ `version_rows`；`App` 标签机制
  （`open_note` / `open_relations` / `open_history` / `activate_tab` / `close_tab` + `tabs_changed`）
  与 `relations` / `versions` 模型 + `restore_version`；新增 `components/tabbar.py`（`TabBar`）、
  `pages/relations.py` / `history.py`；`Shell` 中央改为「标签条 + 页面栈」，右键菜单加关系/历史。
  ruff/mypy/274 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **迁移③：格式工具栏接编辑器**：`NoteEditor.apply_tool`（bold/italic/underline/
  strike、对齐、标题、缩进、列表、引用/代码、清除行内/段落）——**行为接 `QTextEdit`，元数据复用内核
  注册表**；新增 `components/formattoolbar.py`（按 `PRESET_LAYOUT` + `tool_info()` 渲染两行，
  发 `tool_triggered(id, source)`）；  `Shell` 笔记页加工具栏接编辑器。ruff/mypy/275 测试全绿（覆盖率 82%）。
- 2026-09-18 · 已定 · **迁移④：窗口机件与搜索/标签/回收站**：`App` 加 `tags` / `search_results`
  模型与 `reload_tags` / `search_notes` / `show_trash` / `toggle_trash` / `empty_trash` / `restore_note`；
  新增 `components/chrome.py`（`TitleBar` / `StatusBar`）、`components/commandpalette.py`
  （`CommandPalette`，`Ctrl+P`，命令 + 笔记搜索）；新增 `pages/tags.py` / `search.py`；
  `Shell` 改 `VBox`（标题栏 + 活动栏/三栏 + 状态栏），活动栏加搜索/标签，导航右键加恢复/回收。
  ruff/mypy/277 测试全绿（覆盖率 82%）。
- 2026-09-18 · 已定 · **收尾：入口切 Widgets、删 QML**：`ui/app.py` 重写为 Widgets 单入口
  （`open_vault` / env 辅助并入）；删除 `ui/qml/`、`ui/backend.py`、`ui/tools.py`、`ui/views/`、
  `tools/preview_qml.py` 与 `tests/ui/test_backend.py` / `test_smoke.py`；`packaging/cairn.spec`
  改为携带 `config/`（主题配置）；`ui/__init__` 说明更新。ruff/mypy/234 测试全绿（覆盖率 84%）。
  剩余小件：分享/档案/口令弹层、多选批量、拖拽；以及**视觉对齐**。
- 2026-09-18 · 已定 · **迁移⑤ + 视觉首版**：`NavigatorDelegate`（组 = 文件夹图标 + 标题；
  笔记 = 标题 + 预览 + 时间，选中/悬停底色，令牌取色）；`GroupNode` 带 `preview` / `updated`；
  `App` 加 `favorite_many` / `trash_many` / `toggle_homepage` / `set_group_key` / `unlock_group`；
  `Shell` 右键支持多选批量、公开主页、设置组口令。ruff/mypy/234 测试全绿（覆盖率 83%）。
- 2026-09-18 · 已定 · **迁移收尾 + 视觉首轮**：`App` 加档案（设置文件存储：`profiles` / `current_profile`
  / `create_profile` / `switch_profile`，`profiles_changed`）与分享（`share_targets` / `has_share` /
  `toggle_share`）；`NavigatorTree` 支持拖拽入组（自定义 mime，`node_dropped`）；`Window` 标题栏「档案」
  chip 菜单、右键分享子菜单、`_on_node_dropped`；`config/theme/github-*.json` 加容器 `style` 规则
  （标题栏 / 状态栏 / 导航 / 检查器 / 标签条 / 格式栏背景）。修 `UniformRowHeights` 与标题栏撑开。
  ruff/mypy/235 测试全绿（覆盖率 82%）。
- 2026-09-19 · 已定 · **声明式 UI 描述层首版（`cairn.ui.decl`）**：新增 `src/cairn/ui/decl/`——
  语法层 `Node/Layout/Display/Page/Component`（交替规则校验 + 意图边 `on/emit`）；
  配置层 `UiConfAttribute`（默认 / 覆盖 / 重定向 / 失效）与 `Theme` 令牌引用（`token.*`，禁硬编码）；
  `Scope` 隔离；translator 注册表 + `Compiler`（描述树 → Qt 树，**单向一次**，无 reconciler）；
  布局词汇 `VBox/HBox/Grid/Table/Stack`、组件词汇 `Label/Button`、逃生舱 `Raw`；
  组合根 `decl.App` 与最小示例 `build_demo`；入口加 `--decl`（含离屏冒烟）。
  ruff/mypy/286 测试全绿，覆盖率 83%（decl 包 100%）。
- 2026-09-19 · 已定 · **decl 路由 / 页面宿主 / 生命周期**：新增 `decl/router.py`（`PageRegistry`，
  route → Page 工厂）与 `decl/host.py`（`PageHost` + `PageHostWidget`：`QTabBar` + `QStackedWidget`，
  **懒构建**——首次显示才建控件，切换触发 `Page.on_enter/on_leave`，单页隐藏标签栏）；`Page` 加
  生命周期钩子；`build_demo` 改为标签页示例。ruff/mypy/303 测试全绿，覆盖率 83%。
- 2026-09-17 · 已定 · **格式工具栏溢出抽屉改造**：由贴边 `Rectangle`（被正文压住、无动画）改为
  QtQuick.Controls `Popup` 覆盖层（不压正文、点外部/Esc 自动回收），内容改按类别分组的紧凑工具格
   （`DrawerTile`：图标/文本 + 标签），加 `enter`/`exit` 淡入淡出。附：Qt 6 的 `Popup` 打开是
   方法 `open()`、属性是 `opened`（只读），不能用 `open: bool` 绑定。`--smoke` 与离屏预览通过。
- 2026-09-19 · 已定 · **目录结构重定（去 `cairn.` 前缀）**：内核迁为 `src/` 下顶层包
  `conf` / `core` / `feature`（+ 实验 `net` / `server`）；`core/store → core/storage`、
  `domains → feature`、`comm → net`，`cairn/types` 并入 `core/types`；`mypy_plugin` 全名、
  `pyproject`（wheel 包 / isort / per-file-ignore / 覆盖率目标）、README / AGENTS / 架构文档同步。
  UI 源码删除后连带删除 `tests/ui/**` 与引用 UI 的工具（`preview_widgets` / `gen_theme_schema`）。
  内核 ruff/mypy 全绿，149 测试通过、覆盖率 87%。
- 2026-09-19 · 已定 · **UI 内核设计总纲立项**：新增 `docs/architecture/ui-kernel.md`（草案 v0.1）——
  确立「数据内核 / UI 内核」两套体系；UI 内核 = 数据直通 + 对象驱动生成 + 事件绑定 + 统一 Config；
  技术路线 Widgets 宿主 + QML 岛；直通经内核信号原语（预埋目录 `src/core/signal/`，`EventBus` 为过渡）
  + 投影 + 命令，单向数据流。核心约束：**各司其职 = 领域契约 `fields`/`actions`/`signals`**；
  **Bucket/Block 与 UI 正交**（UI 不 import `core.storage`/`feature`，契约不长在 `Block` 上，经中立
  `FieldSpec` 投影）；验收指标「加字段 UI 改 0~1 处」。
  记入 `decisions.md`「UI 内核（2026-09-19，重定）」；`progress.md`「UI 重建」改为 M0–M3 分期，
  并清掉已修复的过期条目（`Vault.put_block` 不发 `ObjectPut`）。
- 2026-09-19 · 已定 · **UI 内核：交付单元 `Facet` + `Bind` 模型定稿**（写入 `ui-kernel.md` §4/§5）：
  生成器由 `Page` 定名 **`Facet`**（`Page` 退为内层页面层）；`Facet.__init__` 只声明**属性配置 + 绑定**；
  `Bind(self).add(UI 信号, 领域 Signal | 本类方法)`，**编译期校验**；Qt 物理 / 控件事件统一包成 `Signal`；
  交付 = 直接交 App（组合根）编译挂载。总目标定为「更便捷、更快、更轻量、更少工作量」。
- 2026-09-19 · 已定 · **UI 内核：信号 / Facet 自包含 / Config 定稿**（`ui-kernel.md` §3.1/§4/§6）：
  `core/signal` = 现有 `EventBus` 升级（存储事件 + 语义信号两层，域间不 import）；`Facet` 自包含
  主题等、不自包含布局 / 部件，`set`（设形态）/ `add`（加持有）语义不可混；产物 = 对象本身直接交 App
  （不序列化）；Config = JSON，App 认识所有 Facet → 自动生成 schema，含布局参数（拖布局 = 改文件）。
- 2026-09-19 · 已定 · **移除旧字符串命名信号层**：删 `core/signal/bus.py`（`SignalBus` / `Signal` /
  `SignalEvent` / `check_name` / `Handler` / `SignalData`）与 `Vault.signals` 接线、`tests/core/test_signal.py`；
  `core/signal/` 留空壳作新「统一调用主干」预留目录。理由：字符串命名与「零字符串静态地址树」设计冲突，
  先清地面（删其 11 个用例，全量 149 通过；ruff / mypy / pytest 全绿）。
- 2026-09-19 · 已定 · **通信主干落地（`core/signal`）**：新增 `Signal`（主干 + 地址树 `core`/`feature`）、
  `Domain`（域服务基类）、`@action`（单播动作描述符）、`Topic`（多播信号描述符）、`Action` / `BoundTopic`。
  零字符串寻址 `signal.feature.Note.save(...)`；单播经 `invoke`（**异常透传**）、多播复用 `EventBus`
  （**异常隔离**）；未注册域动作退回直调、多播 `emit` 丢弃 / `subscribe` 报错；每 `Signal` 一作用域。
  新增 `tests/core/test_signal.py`（9 例）。ruff / mypy / pytest 全绿。
- 2026-09-19 · 已定 · **Note 拆「数据 + 域服务」**：`feature/note/types.py` 原 `Note(Block)` 改为
  `NoteData(Block)`（字段 + 纯内容操作），新增 `Note(Domain)` 域服务（`create` / `load` / `list_notes` /
  `save` / `persist` / `update` / `history` / `body_at` / `restore` / `link` / `add_canvas` / `add_access` +
  `changed` 多播）；`tools.py` 类型改 `NoteData`；`feature` / `note` 导出同步；迁移 `tests/feature/*`
  既有用例；新增 `tests/feature/test_note_bus.py`（域服务挂主干 + 多播 + 异常透传，5 例）。
  ruff / format / mypy / pytest 全绿，163 通过、覆盖率 88%。注意：`core/signal` 包此前未纳入 git。
- 2026-09-19 · 已定 · **数据库重构切片 1（命名 + 载体随机命名）**：`core/storage/catalog.py` 表/列改单数直白名——
  `contents → body`（键 `checksum → body_id`）、`blocks → block`（键 `id → oid`）；`packs` 加 `name` 列，
  载体文件改**随机哈希命名**（`[0-9a-z]` 32 位，`_random_pack_name`），废 `000001.pack`；目录版本 `1 → 2`。
  Catalog 方法改名：`find_content/find_body`、`add_content/add_body`、`count_contents/count_bodies`、
  `block_checksum/block_body_id`、新增 `pack_name`；`bucket._pack_path` 按名取载体。测试同步。
  未动：`type` 仍 TEXT、`author/config/meta` 仍在块表、`versions/version_heads/search/relations` 未碰。
  ruff / format / mypy / pytest 全绿，163 通过、覆盖率 88%。
- 2026-09-19 · 已定 · **数据库重构切片 2（整数类型 + 块 data 收口）**：
  - 新增 `block_type(code, name)` 码表，`block.type` 从 TEXT 改为 **INTEGER**；core 预置
    `0=block / 1=part / 2=index`，其余类型在写入时自动登记（`Catalog.type_code` / `type_name`，稳定不复用）。
  - `block` 表去 `author` / `config` / `meta`，合并为单个 **`data` BLOB**（`{attrs, config, author}`）；
    `Bucket._save_block` / `_get` 相应改写（类型码转换、data 编解码）。
  - 未动领域类（仍字符串 `type`，仅存取层转码）；`versions/version_heads/search/relations` 未碰。
  - 记录：`catalog_version` 只标记、**无迁移逻辑**；改已有表须显式迁移。pre-1.0 + dev 库可弃，正式发布前补迁移。
  ruff / format / mypy / pytest 全绿，163 通过、覆盖率 88%。
- 2026-09-19 · 已定 · **数据库重构切片 3（版本去冗余 + 边表 + 领域枚举走索引）**：
  - `core/storage/version.py`：删 `version_heads` 表；head / count 改为从 `version` 表**推导**
    （head = 不被任何 `prev` 指向者）；表名 `versions → version`。
  - `feature/relation.py`：表名 `relations → relation`，新增 **`domain`** 字段（边归属领域）；
    `Note.link` 传 `domain="note"`、`Group._link_relation` 传 `domain="group"`。
  - `catalog.py` 加 `idx_block_type` 索引与 `find_type_code`；`Vault.iter(type=…)` 改走
    `block WHERE type=code`（**不再逐块解码全库**）。
  - **推翻「每域一张表」**：不建 `note` / `project` / `group_index`——`block.type` 整数码即领域枚举索引，
    关系走 `relation`、分组走 `cairn.group` 块；建域表只会复制块内数据。理由见 `decisions.md`。
  ruff / format / mypy / pytest 全绿，163 通过、覆盖率 88%。
- 2026-09-19 · 已定 · **总线收成一根主干**：`Vault` 不再自建 `EventBus`，改持 `Signal`；
  `Vault.signal` 为唯一主干，`Vault.events` 即 `signal.events`（投递器）。存储事件
  （`ObjectPut` / `ObjectDeleted`）与领域信号自此**同一条总线**，域服务经 `vault.signal.register(...)` 挂载。
  ruff / format / mypy / pytest 全绿，163 通过。
- 2026-09-19 · 已定 · **`EventBus` 并入 `core/signal`**：`src/core/events.py` → `src/core/signal/events.py`
  （`from .types` 改 `..types`）；`bus.py` / `service.py` 改相对导入；`core.signal.__init__` 统一转出
  `Event` / `EventBus` / `Handler` / `ObjectPut` / `ObjectDeleted` / `Subscription`。`core/__init__` 与
  `Vault` 改从 `core.signal` 导入。**信号层现在一处可导入**（`EventBus` 不再单飞）。
- 2026-09-19 · 已定 · **App 层落地 + 目录重定（用户主导）**：新增 `src/app/`（App = 组合根 / 编排：`__main__.py`、
  `win/{main,backend,windows}`、`linux/`）；`src/ui/` → `src/ui_tools/`（界面工具层）；新增 `src/core/conf/`
  （配置 / 常量，`core.py` 含 `FORMAT_VERSION` / `TOML_NAME` / `VAULT_META_CONTEXT` / `VERSION_WINDOW_MS`）；
  **删除** `src/conf`、`src/net`、`src/server`、`src/ui`；撤除 `src/kernel.py` / `src/main.py`（编排归 App）。
  收尾：修 `core/__init__` 半截导入、`ui.` → `ui_tools.` 引用、补新建占位文件 SPDX 头与 docstring、
  `pyproject` 的 wheel packages / isort。ruff / format / mypy / pytest 全绿，211 通过。
- 2026-09-19 · 已定 · **架构文档回写（事实修正）**：`storage.md` 改表 / 列（`block` / `body` / `block_type` /
  `block.data` / 随机 pack 名 / 去 `version_heads` / `relation.domain`）；`domains.md` 改「数据 + 域服务」与当前路径；
  `kernel.md` 加 §1.6 通信主干（`core/signal` 静态挂载）；`data-model.md` / `ui-kernel.md` 加现状导引。
  待回写：`access.md` / `network.md` / `ecosystem.md` / `ui-theme.md` / `note-model.md`。206 通过。
- 2026-09-19 · 已定 · **领域拆分（Project / Group）**：`ProjectData(Block)` + `Project(Domain)`（创建 / 载入 / 更新 /
  成员关系）、`GroupData(Block)` + `Group(Domain)`（创建 / 增删 / 重排 / 嵌套解析）；`group` 模块函数改用 `GroupData`；
  `feature` 导出两套；测试迁移。至此 **note / asset / canvas / project / group 五域口径统一**（数据 + 域服务）。
  ruff / format / mypy / pytest 全绿，206 通过。
- 2026-09-19 · 已定 · **领域拆分（Asset / Canvas）**：按 note 口径拆「数据 + 域服务」——
  `AssetData(Block)` + `Asset(Domain)`（入库转码 / 载入）、`CanvasData(Block)` + `Canvas(Domain)`（创建 / 载入）；
  `note/model` / `note/types` / `note/__init__` 改用 `CanvasData`；`feature` 导出两套；测试同步。
  ruff / format / mypy / pytest 全绿，206 通过。
- 2026-09-19 · 已定 · **清理 `Vault` 死 API**：删 `put` / `put_meta` / `versions` / `read_version` /
  `restore_version` 与 `Source` / `_read_source`；并清加密时代残留 `lock` / `unlock` / `is_locked`、
  `create(path, passphrase)` 的 `passphrase` 参数；删 `core.types.VersionInfo`（无活引用）。
  测试改用 `put_block(Block(...))`；删 `tests/core/test_versions.py`；门禁全绿，206 通过。
- 2026-09-19 · 已定 · **App 层接线**：`src/app/__init__.py`（`Feature` 静态域容器 + `build(vault)` 组合
  Session/App/Facet）、`src/app/facets.py`（`NoteFacet`，App 侧领域 UI，不 import feature）、
  `src/app/win/main.py`（Windows 入口：QApplication + `build_window` + show）、`src/app/__main__.py`（按平台分发）。
  新增 `tests/app/`。`ui_tools` 原地不动（工具）。ruff / format / mypy / pytest 全绿，210 通过。
- 2026-09-19 · 已定 · **清理：撤销 `feature/_shared` + 清空 `ui_tools` 主导件**：删 `src/feature/_shared/`
  （`relation`/`provenance`/`signature` 回 `feature/` 顶层；跨域编排归 App）；删 `ui_tools/app.py`、`ui_tools/note.py`
  与对应测试（`ui_tools` 是工具箱，不放入口 / 领域 Facet）。ruff / format / mypy / pytest 全绿，209 通过。
- 2026-09-19 · 已定 · **领域共享层 `feature/_shared/`**：把 `relation` / `provenance` / `signature` 从 `feature/` 顶层
  （看着像域）移入 `feature/_shared/`（横跨多域的共享设施）；更新 `feature/__init__` / `group` / `note` / `project` /
  `provenance` 引用与测试。域不再横着 import 兄弟。ruff / format / mypy / pytest 全绿，211 通过。
  剩余横向依赖 `note → canvas`（待定归宿）。
- 2026-09-19 · 已定 · **领域树归位到应用内核**：`main.py` 只做 boot；新增 `src/kernel.py`（`Feature` 静态领域容器 +
  `Kernel`：握 `signal`、挂 `feature`）——领域树声明落在**应用内核侧**（`core` 不许认识 `feature`，故不能放进
  `core.signal`；入口也不该定义它）。ruff / format / mypy / pytest 全绿，211 通过。
- 2026-09-19 · 已定 · **去掉动态注册，改静态挂载**：删 `core/signal` 的 `Namespace` / `Signal.register` /
  `_domains` / `domains()` / `Domain.namespace`；`Signal` 暴露 `core` / `feature` 属性（组合根普通赋值）；
  `Domain` 加 `bind(signal)` 显式绑总线。组合根 `src/main.py` 用静态 `Feature` 容器（`Note: Note` + 构造赋值）。
  多个测试改为静态挂载 / `bind`。ruff / format / mypy / pytest 全绿，211 通过。理由：动态注册无人受益（见 decisions）。
- 2026-09-19 · 已定 · **UI 列表 + 模型桥 + 变更自动刷新**：`Session.model(loader)` 建类型化模型（主干一变即重算并通知）；
  `ui/component/atoms.py` 加 `List` 原子（持 `Model` + `row` 行文本）；新增 `ui/core/qtmodel.py` `QtListModel`
  （`Model[T]` → `QAbstractListModel`，变更整表 reset）；`ui/core/qt.py` 加 `list` 翻译器（`QListView`）。
  新增 `tests/ui/test_list_model.py`（新增笔记 → 列表行数自动 +1）。ruff / format / mypy / pytest 全绿，212 通过。
- 2026-09-19 · 已定 · **UI 底层补口**：`Facet.node_paths()` 对同名同类兄弟路径去重（首原名、余追加 `#n`），
  修 schema 路径碰撞；新增 `tests/test_architecture.py`（红线：`ui` 不 import `feature` / `core.storage` / `core.vault`）。
  ruff / format / mypy / pytest 全绿，211 通过。
- 2026-09-19 · 已定 · **UI 信号 + 绑定落地**：`UiSignal` 加 `owner`；`Component.ui_signal(name)` 声明信号，
  `Button.clicked` / `Field.text_changed` 已声明；`Node` 加 `bind_widget` / `widget`（编译期回填目标控件）；
  Qt 翻译器回填控件；`WindowHost` 编译绑定（`source.owner.widget` 上的同名 Qt 信号 → target）——**按钮点击真连上动作**。
  另：`main.py` 改从地址树取对象（`vault.signal.feature.Note`）再注入 `NoteFacet`。ruff / format / mypy / pytest 全绿，210 通过。
- 2026-09-19 · 已定 · **真实组合根 + `NoteFacet`**：新增 `src/ui/note.py` `NoteFacet`（收**注入的**笔记域服务、
  **不 import `feature`**；经 `Session.projection` 投影出列表条目）与 `src/main.py` 组合根（打开 `Vault` →
  `vault.signal.register(Note)` → `Session` → `App` → `mount(NoteFacet)` → `build_window`）——**只有入口认识领域**。
  新增 `tests/ui/test_note_facet.py`。ruff / format / mypy / pytest 全绿，209 通过。
- 2026-09-19 · 已定 · **UI 路由宿主 + 可运行入口**：`ui/core/qt.py` 加 `WindowHost`（`App` → `QMainWindow` +
  `QStackedWidget` 内容区，`show(route)` 按 `App.navigate` 切换；`build_window` 仍返回窗口）。新增 `src/ui/app.py`
  （`build_demo` / `main`：组合根 demo，**不依赖领域**，验证"声明树 → 窗口"整链）。新增 `tests/ui/test_app_entry.py`。
  修正：`Facet` 收注入对象、**不需要 import 领域**，UI 红线无需放宽。ruff / format / mypy / pytest 全绿，208 通过。
- 2026-09-19 · 已定 · **UI 最小 MainWindow**：`ui/core/qt.py` 加 `build_window(app)`——`SuperLayout` 落成
  `QMainWindow`（标题栏 / 导航 + 内容 + 检查器 / 状态栏；内容用 `QStackedWidget` 装已挂载页面）；
  入口三件套 `build` / `build_compiler` / `build_window`。新增测试。ruff / format / mypy / pytest 全绿，206 通过。
- 2026-09-19 · 已定 · **UI 主题（token → QSS）**：新增 `ui/core/theme.py`（`Theme`：`token` 封闭词表 +
  CSS 式 `styles`；`resolve` 展开 `token.*`；`to_qss()` 把 `widget.<kind>[:state]` 编译为
  `QWidget[cairnClass="<kind>"][:state]`；`apply(qapp)` 全局套用）；`ui/core/qt.py` 给每个控件打
  `cairnClass` 动态属性。新增 `tests/ui/test_theme.py`。ruff / format / mypy / pytest 全绿，205 通过。
- 2026-09-19 · 已定 · **UI 组件原子**：`ui/component/atoms.py` `Label`/`Button`/`Field`/`Divider`/`Chip`（各带 `STYLABLE`/`STATES` 词汇元数据）；`ui/core/qt.py` 补对应翻译器（QLabel/QPushButton/QLineEdit/QFrame）。新增 `tests/ui/test_atoms.py`。ruff / format / mypy / pytest 全绿，202 通过。
- 2026-09-19 · 已定 · **UI 内核 · Qt 桥 + 最小翻译器**：新增 `ui/core/bridge.py`（`Bridge(QObject)`：
  `Session` 变更 → Qt `changed` 信号）与 `ui/core/qt.py`（`build_compiler`：`page`/`layout`/`vbox`/`hbox`/
  `grid`/`split`/`stack`/`component` → QWidget 树）。`Translator` 由 `Protocol` 改 **`Callable` 类型别名**；
  `Page` 的布局改为**结构子节点**（编译树连通）。`ui.core` **不 eager 导入** Qt 模块（未装 Qt 仍可导入内核）。
  新增 `tests/ui/conftest.py`（offscreen `QApplication`）+ `tests/ui/test_qt.py`。ruff / format / mypy / pytest 全绿，197 通过。
- 2026-09-19 · 已定 · **UI 内核底层 · 配置加载**：新增 `ui/core/config.py` `apply_config(schema, data, group)`——
  `{路径: {项: 值}}`，路径可**从领域起写**、经 schema 校验后写进节点 `Conf`（`attr` / `theme`）；
  不可寻址 / 未知组即报错。`Schema` 增记路径 → 节点（`node()`）；`Facet.node_paths()`、`App.schema()` 带节点。
  新增 `tests/ui/test_schema.py` 用例。ruff / format / mypy / pytest 全绿，193 通过。
- 2026-09-19 · 已定 · **UI 内核底层 · 绑定编译 + 模型**：`Bind.compile()`（源须 `UiSignal`、目标须可调用，
  否则报错）与 `Facet.compile_bindings()`（Facet + 默认页 + 各页面汇总）；新增 `ui/core/model.py`
  （`Model[T]` 类型化可观察列表：append/replace/remove/clear + `watch` 返回取消）；`Session.projection[T]`
  泛型化。新增 `tests/ui/test_bind_model.py`。ruff / format / mypy / pytest 全绿，189 通过。
- 2026-09-19 · 已定 · **UI 内核底层 · 配置路径 schema**：新增 `ui/core/schema.py`（`Schema`：规范形式
  `app.<域>.<page>.<layout>.<com>…`；`resolve` 支持**从领域起写 + 后缀补全**，未命中 / 歧义即报错）；
  `Facet.paths()` 由领域树导出相对路径、`App.schema()` 汇总。新增 `tests/ui/test_schema.py`。
  确认：PyQt 无"编译层"（Shiboken 运行期绑定、QSS/.ui 运行期解析、QML 可预编译）；
  `Compiler`/`Translator` 预留**构建期静态化**缝（生成 `.ui` / 静态 Python / QML，内核不改）。
  ruff / format / mypy / pytest 全绿，183 通过。
- 2026-09-19 · 已定 · **UI 内核底层（通用机制）**：`Node` 加 **kind 注册表**（`__init_subclass__` 自动登记，
  冲突报错）、**词汇元数据** `STYLABLE`/`STATES`、**父子链与点分路径**（`parent`/`path()`/`walk()`）；
  新增 `ui/core/registry.py`（`kinds` / `vocabulary`）、`ui/core/signal.py`（`UiSignal`：UI 侧信号代理占位）、
  `ui/core/compile.py`（`Translator` 协议 + `Compiler` 注册表，深度优先单向编译）。新增 `tests/ui/test_kernel.py`。
  此后布局 / 页面 / 组件只是"声明 `kind` + 元数据"，配置 / 编译 / 绑定机制通用。
  ruff / format / mypy / pytest 全绿，179 通过。
- 2026-09-19 · 已定 · **UI 内核骨架 · Facet 声明层（Qt-free）**：`src/ui/` 新增——
  `ui/core/errors.py`、`conf.py`（`Conf`：`theme` 封闭 / `attr` 开放，`set` / `add`）、`bind.py`（`Bind` 登记处）、
  `node.py`（`Node`：名称 + 配置 + 子件 + **能力声明** `addable` / `capacity` / `stretch` / `variable` / `actions`）、
  `facet.py`（`Facet`：`page(page, route)` 路由表 + 反表、`set`/`add` 默认页、`bind` / `conf`）、
  `app.py`（`App`：根壳 `SuperLayout` 命名区域 + `mount(facet, slot)` + `navigate`）；
  `ui/layout/layout.py`（`Layout` + `VBox`/`HBox`/`Grid`/`Split`/`Stack`）、`ui/component/component.py`（`Component`）、
  `ui/page/page.py`（`Page`）。新增 `tests/ui/test_facet.py`（7 例）。ruff / format / mypy / pytest 全绿，173 通过。
- 2026-09-19 · 已定 · **UI 目录骨架**：`src/ui/` 分 `core`（内核：`Session` / `App`）/ `layout` / `page` /
  `component` / `qml` 五个子包（后四个先建空壳，SPDX 头齐全）；`ui/core/session.py` 改从 `core.signal` 导入；
  测试 `tests/ui/test_session.py` 改 `ui.core.session`。 ruff / format / mypy / pytest 全绿，166 通过。
- 2026-09-19 · 已定 · **UI 内核重建 · 接入点骨架（Qt-free）**：新建 `src/ui/`——
  `Session`（消费主干：订阅 `Signal.events`，维护投影缓存，变更即整体失效并通知观察者；`watch` 返回取消函数；
  `close` 收订阅）与 `App`（组合根，持 `Session`）。**不 import `feature`、不碰 `Vault`**，只吃 `Signal`；
  不带 Qt。新增 `tests/ui/test_session.py`（3 例）。ruff / format / mypy / pytest 全绿，166 通过。
- 2026-09-21 · 已定 · **Windows 壳骨架首片**：新增 `src/app/win/windows/`——`theme.py`（软质感 token → QSS）、
  `shell.py`（顶带 / 舞台 / 任务栏三带 + 卡片 / 详细两种密度 + 软卡片 delegate）、`samples.py`（样例卡片）；
  `win/main.py` 入口切到 `Shell`（暂用样例数据）；`tools/preview_shell.py` 渲染 PNG 自检；
  `tests/app/test_shell.py`（4 例）。ruff / format / mypy 全绿，209 测试通过、覆盖率 87%。
- 2026-09-21 · 已定 · **壳重构：回到 `ui_tools` 管线 + 真实数据 + config 主题**（修正上一版裸 Qt 壳）：
  部件进 `ui_tools`——`Heading` 原子、`component/structure.py`（`TopBar` / `TaskBar` / `CardStage`）、
  `core/cardview.py`（卡片视图 + 委托）、`core/node.py` 加 `Node.action` / `NodeAction`、
  `core/theme.py` 加 `load_theme`、`core/qt.py` 加 `topbar`/`taskbar`/`stage` 翻译器与 stretch，
  `SuperLayout` 加 `topbar` / `taskbar` 区域；`app/win` 改为 `windows/ShellFacet`（声明三带）+
  `backend`（笔记卡投影）+ `__init__.build` 组合根；`config/theme/github-{dark,light}.json` 改为当前
  部件词汇与壳样式；删 `app/facets.py` 与裸 Qt 壳（`windows/shell.py` 重写、`samples.py` 删）。
  ruff / format / mypy 全绿，209 测试通过、覆盖率 87%。
- 2026-09-21 · 已定 · **层级校正：`App` = 根、`Facet` = 子件**：`ui_tools.core.App` 暴露区域句柄
  （`self.topbar` / `content` / `taskbar`…）+ App 级 `self.bind`；`SuperLayout` 的 `TopBar`/`TaskBar`
  成为根壳区域（`core/app.py`），`WindowHost` 直接编译区域节点（`node` → VBox 兜底）；`CardStage`
  留作内容组件。`app/win` 重排：`windows/app.py`（`CairnApp`，App 级定义顶带 / 任务栏并 `mount` 笔记域）、
  `windows/notes.py`（`NoteFacet`，内容工具条 + 卡片舞台）、删 `windows/shell.py`；密度切换移入笔记
  `Facet`（不跨层）。ruff / format / mypy 全绿，209 测试通过、覆盖率 87%。
- 2026-09-21 · 已定 · **App 收口启动样板**：`ui_tools.core.qt.run(app)`（套主题 / 建窗 / `exec`）；
  `CairnApp.__init__(vault)` 内部完成 Feature / Session / 根布局 / `mount`，并加 `CairnApp.open(root)`；
  `app/win/main.py` 收成一行 `CairnApp.open().run()`；`app/win/__init__` 去 `build`，测试与
  `tools/preview_shell.py` 改用 `CairnApp(vault)`。ruff / format / mypy 全绿，209 测试通过、覆盖率 87%。
- 2026-09-21 · 已定 · **根结构重定：大方框 + 格子 + 槽**：删 `SuperLayout` / `TopBar` / `TaskBar`
  与全部预置区域；新增 `core/slot.py`（`Slot`：`expects` + 行为 `stretch`/`scroll`/`align`/`hidden`/
  `locked`/`capacity`）；`App` 改为持 `root` 大框 + `slots()` + `add(facet)`（按 `expects` 填
  `facet.parts()`）；`Node.add` / `Page.add` / `Facet.add` 泛型化（免 cast）；`Facet` 加 `parts()`；
  新增 `Surface` 组件（带外观容器）；`WindowHost` 改为编译 `app.root`。`CairnApp` 自己搭结构与槽，
  `NoteFacet.parts()` 供 `nav` / `page`；主题 `widget.topbar`/`taskbar` → `widget.surface`。
  ruff / format / mypy 全绿，209 测试通过、覆盖率 87%。
- 2026-09-21 · 已定 · **`Attr` / `Data` 迁入 `core.types`**：从 `core/storage/block.py` 移到
  `core/types/attr.py`（去掉对 `Block` 的注解依赖，改 `Any`）；`core.types` 转出，`core.storage`
  re-export 兼容；mypy 插件 `ATTR_FULLNAME` 跟着改（`core.types.attr.Attr`）。
  ruff / format / mypy 全绿，209 测试通过、覆盖率 87%。
- 2026-09-21 · 已定 · **领域降级 + 最小类型表**：删 `Asset` / `Canvas` / `Group` 的 `Domain` 服务
  （构造入口改为 `AssetData.create` / `CanvasData.create` / `GroupData.create`，组操作成 `GroupData`
  方法）；新增 `core/types/kind.py`（`TypeInfo` + `register` / `type_info` / `types` / `collect_fields`），
  `Block` / `Domain` 定义时登记（`(type, role)` 分键，域与数据可同名）；`Note` / `Project` 声明
  `type` / `name` / `data`(依赖数据结构)。新增 `tests/feature/test_kind.py`。
  ruff / format / mypy 全绿，215 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **最小类型表补 `unit`（最小数据单元）**：`TypeInfo.unit` 指向既有数据类型的
  `type`；域上 `light = XxxData` 显式绑定（`Note` / `Project`），缺省回落 `cls.type`；UI 顺指针取
  `fields`，不复制字段表。216 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **最小数据单元改多值**：`light` 收单值或列表/元组 → `TypeInfo.units`（`type`
  名元组）；新增 `unit_infos`（顺下取单元）/ `domain_of`（反查所属域），公共锚点 `Block`。
  218 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **领域文件归位（第一批）**：新增 `feature/shared/`（asset / canvas / group /
  signature / relation / provenance / base 迁入，`shared/__init__` 转出）；`feature/__init__` 改从
  `.shared` 转出；删 `note/note.py` 残留；`note/edit.py` 拆成 `note/edit/`（body / text / style，
  `__init__` 兼容转出）；调用方改子模块具名导入。218 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **note/types.py 拆包**：→ `body.py`（`NoteBody`）/ `data.py`（`NoteData` +
  `canvas_ref` / `access_ref`）/ `service.py`（`Note` + `_search_text`）；纯搬运、行为不变；
  `note/__init__` 与 tests 改从 `feature.note` 顶层导入；删 `types.py`。
  218 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **笔记操作归位**：编辑操作（`set_text` / `set_body` / `blocks` / `reorder` /
  行级增删拆合 / 样式 / 段落 / `_append_marker`）从 `NoteData` 迁到 `Note`（以 data 为首参）；
  `NoteData` 只留字段 + 读视图（`body_hash` / `text` / `style` / `paragraph` / `references` / `_state`）；
  `note/tools.py` 改 `run(svc, data, ctx)` / `state(data, ctx)`，测试同步。
  218 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **类型枚举落地**：新增 `feature/shared/kinds.py`（`Kind(StrEnum)`：note / project /
  canvas / asset / group）；`NOTE_KIND` 等常量与各数据类型 `type` 改指枚举；类型表
  `register` / `type_info` / `domain_of` 按 `str()` 归一（枚举与字符串可互换，第三方可继续用字符串）。
  219 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **数据描述合并 + Domain 声明重定 + `Show`**：`note/body.py` + `data.py` +
  `model.py` 并成 `note/data.py`（`Style` 挪 `edit/style.py`，避免 edit↔data 环）；`Domain` 的
  `name` 改为模块路径（解析键，非显示名）、`data` 收**数据类元组**、`light` 改 list；新增
  `ui_tools/core/show.py`（L0 归集 / L1 分组 / L2 字段呈现 / L3 body 感知；L4 不做）。
  222 测试通过、覆盖率 88%。
- 2026-09-21 · 已定 · **文档回写（类型 / 领域口径）**：`domains.md` 重写为 v0.3（域 / 数据两分支、
  `Kind` 词表、域与数据的标准形、日志）；`data-model.md` 类型名去 `cairn.` 前缀、§12.2 映射表按
  「域 + 数据 + 共享件」重列；storage / access / note-model / ui-kernel / ui-theme 同步；
  `feature/shared/` 路径与信号命名（`Topic` 句柄）一并更新。
- 2026-09-21 · 已定 · **Kind 重定（Feature / Data，去前缀）**：`Kind.Feature`（note / project）+
  `Kind.Data`（notedata / projectdata / canvas / asset / group），plain `Enum`；域与数据不再共用
  字符串。core 的 `block` / `part` / `index` 与 `relation` 同步去前缀；新增 `core.types.type_name`
  归一（贯穿 block / catalog / vault / 类型表）；`NOTE_KIND` 等常量改指枚举。
  AGENTS.md 架构分层同步。219 测试通过、覆盖率 88%。

