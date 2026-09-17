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
- 2026-09-17 · 已定 · **格式工具栏溢出抽屉改造**：由贴边 `Rectangle`（被正文压住、无动画）改为
  QtQuick.Controls `Popup` 覆盖层（不压正文、点外部/Esc 自动回收），内容改按类别分组的紧凑工具格
  （`DrawerTile`：图标/文本 + 标签），加 `enter`/`exit` 淡入淡出。附：Qt 6 的 `Popup` 打开是
  方法 `open()`、属性是 `opened`（只读），不能用 `open: bool` 绑定。`--smoke` 与离屏预览通过。
