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
