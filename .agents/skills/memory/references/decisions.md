<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 决策

> 2026-09-16 存储层重写：早期「加密对象池 / 双源 / 结构库半加密 / 多空间 / manifest 版本链」
> 相关决策**全部作废**（已从本表移除）。以代码与 `docs/architecture/*.md` 为准。

## 存储（2026-09-16 重写）

- 已定 · **桶 + 块**是唯一内核：`Bucket`（载体/文件系统管理类）+ `Block`（存储单元）；
  其余一切（note/asset/project/画板/索引/变更）都是块或其属性。
- 已定 · **本地不加密**（明文落盘）；加密只用于传输/服务端。删除 crypto / manifest / space / 分块池。
- 已定 · 块字段：`id`（稳定 OID，锁死）/ `checksum`（内容哈希，十六进制串）/ `type` / `body` /
  `attrs` / `config` / `author` / `size` / `created` / `updated`。哈希一律是字符串。
- 已定 · 去重在**领域层**（note 只与 note、project 只与 project 比 checksum）；分片块不去重。
- 已定 · 分片由块自带（`Bucket.put_content`）：大内容 = 分片 + 索引块。
- 已定 · 目录（catalog DB）是块位置的唯一真源；pack 只追加、顺序命名、写满封口。

## 领域（2026-09-16）

- 已定 · 领域结构**直接继承 `Block`**（无中间层）；通用读写（save/load/list/oid/info）在 `Block`。
- 已定 · `Attr(item=)` 让列表字段类型化：存储是紧凑数据，取出来是类型化对象。
- 已定 · `composition` 并入 note（移除独立对象）。
- 已定 · **组（`cairn.group`）**：独立块；域 ID **`gid`** 与块 `oid` 分开（不改 `Block`）；
  `group: list[str]` 有序子项（组存 gid、其余存 oid，可无限嵌套）；成员**两套都存**
  （列表存结构顺序 + `relations` 存 `contains` 反查）；`lock` 锁编辑；`owner` / `member` / `key`
  为社区「有限编辑组」预埋（`User` 系统落地前用字符串）。
- 已定 · 关系是**一等 DB 行**（`relations` 表）：`derived-from` / `references` / `contains` 等多类型，
  用于引用拓扑；`provenance` 查表。
- 已定 · note 正文 = `list`（文字段 + 占位符）；样式等长对齐；画板/多媒体用
  `{"canvas": n}` / `{"access": n}` 占位。
- 已定 · 画板 = **数值序列**：`Canvas{graphics, links}`、`Graphic`（预制编号 + 中心点 + 缩放/旋转 +
  点路径 + `Paint`）；连线只存图形下标 + 线型，走线派生。
- 已定 · 预制图形**外置**：`config/shapes.json` + 生成器；形状是生成器概念，点是渲染概念。
- 已定 · 标签用 dict（`{键: 值}`）；作者 = `author`（原作者）+ `authors`（有序署名）。
- 已定 · 笔记版本 = **增量 diff 落 DB**（`versions` 表），保留窗 30 天、惰性压实；块不管版本。
- 已定 · `Asset` 入库先转码到统一编码（草案；图片/音频走不传染库，视频暂不转码）。

## 笔记编辑模型 / 版本引擎（2026-09-17，M0）

- 已定 · 正文 `body = list[{"id","v"}]`（**一元素 = 一行/一块**），元素带稳定行 id；`v` 为
  文字或嵌入占位（`{"canvas":n}` / `{"access":n}`）。行序列保序用 list（canonical CBOR 会排序 map key，dict 不能保序）。
- 已定 · 样式是**非对称覆盖层** `style = {行id: [ {区间(tuple): Style} ]}`；行内区间可叠加，
  后层压前层；规范化为不重叠、有序、去默认。行内加粗不拆 body。
- 已定 · 行 id 用 ULID（`Oid`），生成即锁死；行增删/重排不动样式，**无下标漂移**。
- 已定 · 内容地址 **cID（checksum）剥离行 id**：同文同样式即同签名 → 纯复制/同文可去重；
  改一字即不同。id 不参与内容计算。
- 已定 · 版本用**通用引擎 `VersionStore`**（`core/store/version.py`，block 亲和）：版本 id =
  `blake3(canonical({prev, at, sig}))`，`prev` 单亲链；顺序从 head 沿 prev 走，不靠时间/序号；
  第一版记根节点（空补丁）。域提供 `Codec`（digest/diff/apply），笔记 Codec 在 `note/versions.py`。
- 已定 · diff 是**反向补丁**（新→旧），按行 id：`PUT`（载荷=旧值，回放写回）/`DROP`（该行为新版新增）/
  `@order`（仅顺序变化）；未变更行不入补丁。载荷必须是旧值（当前版本只在块里，回放只能倒推）。
- 已定 · 哲学「**笔记残页**」：diff 脱离当前块上下文即失效；压实=永久遗忘；传输必须带 base；
  需要 `fold` 把链折成新版本（尚未实现）。
- 已定 · ID：`id`（块身份，str）+ `oid`（同值，Oid 对象）即可；**不再另立 nid/pid**（已回退）。
- 已定 · 长行不设内核上限，交给 UI：超阈值关自动换行、逼硬回车产生新行。
- 已定 · **body 内容池在桶里**：`checksum = body_hash`（只算 body：文字+样式+占位，剥离行 id），
  `contents(body_hash → 位置)` 即去重池，查找 O(1)；**attrs 随块行存、不参与去重**
  （标题/标签/签名/时间不同不影响同正文去重）。body 与 attrs 分家存储。
- 已定 · **段落 = 行**：**1 个硬行就是 1 段**，不设独立段落实体；段级属性放行元素 `p`，
  字级仍走行内区间 `style`。超长行（等效中文 > 300）由 UI 关软换行、转横向滚动逼硬回车，**不自动拆行**。
- 已定 · **工具 = 基类 + 参数化实例**（`domains/note/tools.py`）；**分组 / 位置是数据**
  （`PRESET_LAYOUT`，将来可用户自定义）。工具栏两行（编辑型字级 / 段级）、纯图标 + 提示、溢出**向下抽屉**。
- 已定 · **工具四分类**（2026-09-17）：`ToolCategory` = 添加 / 编辑 / 命令 / 查询；分类是工具元数据
  （抽屉内分组），两行预设只放编辑型，其余自定义时随便摆。**编辑型 / 添加型**改 note、元数据在
  `domains/note/tools.py`；**命令型 / 查询型**属应用与界面、元数据在 `ui/tools.py`，行为由 UI 回调 `Backend`。
- 已定 · **`Tool.state` 只读三态**（2026-09-17）：`run` 写、`state` 读；`state` 返回 `True` 生效 /
  `False` 未生效 / `None` 混合，供工具栏高亮；四类里只有**编辑型**有可读状态。未实现工具
  `available=False`（UI 置灰、不执行），不假装已存在。
- 已定 · **保存与版本分离**：自动保存只落盘（`Note.persist`）；版本检查点仅在**非连续编辑边界**产生
  （空闲超时默认 5 分钟 / 切换笔记 / `Ctrl+S` / 退出），避免逐次保存堆出大量微小版本。
- 已定 · **`Body` 是容器基类**（`core/store/block.py`）：无 ID、依存于块；自带状态字段 `hash`
  （对 `content()` 求摘要，**只含内容字段**，排除自身状态/时间戳）。内容一变就 `refresh()` 重算并缓存。
  旧描述符改名 **`BodyField`**（裸 body 用 `BodyField()`，结构化用 `BodyField(prototype=...)` 每实例一份）。
- 已定 · **`NoteBody(Body)`**：字段 `text`（行序列）+ `style`（行内样式）；`content()` 剥离行 id，
  故 `body.hash` 只反映文字+样式 → 同文同样式同哈希。`Note.body: NoteBody = NoteBody()`（类型自证，无需标记，
  `Block.__init_subclass__` 自动包成 `BodyField`）；`note.style` 是 `body.style` 的代理。`checksum = body.hash`。
- 已定 · **签名是复合结构（一组字段），不是一段串**：`Signature{alg, author, created, subject, prev, value}`；
  自包含、自校验（改任一字段 value 对不上）。创作签名创建即锁死、`subject` 指向创建时 body_hash（原始结构可找回）；
  变更签名（非原作者、prev 链）为多作者预留。当前 `alg="b3"` 哈希链，日后换 `ed25519` 不破格式。
- 已定 · 字段类型化：写法为 **`field: Attr[T] = 默认值`**（注解即类型、右边即值；`Block.__init_subclass__`
  自动包成描述符）。mypy 靠自研插件 `tools/mypy_plugin.py`（base class hook）把 `Attr[T]` 字段的可见类型
  改写成 `T`，**无需 ignore**；显式描述符字段（`coerce`/`item`）写**裸 `Attr`**，插件不动。
  `title/tags/authors` 属业务字段，已从 `Block` 挪到 Note/Project/Asset（`Block` 只留硬件字段）。
- 已定 · **`Attr` = 属性字段，`Data` = 数据字段**（两者同机制、同存储）。`title/tags/signature` 等描述性
  元数据用 `Attr`；承载数据的 `canvas/access` 用 `Data`（避免"属性"用词错位）。位置不变、仍在块内。
- 已定 · **`Canvas` 升格为块**（`cairn.canvas`，`domains/canvas.py`）：`Canvas(Block)` + `CanvasBody(Body)`
  （`mode` diagram/sketch + 图形 + 连线）；全局内容寻址、去重。note 的 `canvas: list[str]` 存 canvas oid。
- 已定 · **不设 `Access` 类**：外联资源就是 `Asset`（Block）；note 的 `access: list[str]` 存 asset oid（全局去重）。
- 已定 · **数据字段免标记**：裸容器注解自证类型，自动成 `Data` 字段（每实例一份）——
  `access: list[str] = []`、`canvas: list[Canvas] = Canvas.container(list)`。属性仍需 `Attr[T]` 标记。
  `encrypt/shareable` 等硬件配置位未加。

## 工程 / 产品

- 2026-09-14 · 已定 · skill 放 `.agents/skills/`；根 `AGENTS.md` 只做索引；`rules`=约束、`memory`=现状。
- 2026-09-14 · 已定 · 布局契约：三栏 SplitView，属性栏默认收起；列表交互照 VS Code、不做过渡动画。
- 2026-09-14 · 已定 · 删除先入回收站；**版本只记内容变化**（元数据不产生历史）。
- 2026-09-14 · 已定 · 分发：源码与 Windows 桌面 P0（PyInstaller onedir + Inno）；macOS 暂缓。
- 2026-09-16 · 已定 · UI：精简、自然；色盘照 GitHub，圆角与阴影照苹果；中英统一等宽字体
  （链条首为「更纱黑体 / Sarasa Mono SC」）。
- 2026-09-16 · 已定 · 只引不传染许可（MIT/BSD/Apache）的依赖；GPL/AGPL 禁用。
- 2026-09-17 · 已定 · **质量口径 =「企业级-ε」**（企业级略降半档）：mypy strict（`src`+`tools`）、
  ruff `select=ALL` + 逐条有理由的 ignore、`ruff format` 强制、warning 零容忍、覆盖率行+分支 ≥80%。
  中文项目现实豁免：中文标点（RUF001-003/D415）、方法级 docstring（D102/105/107）、领域词汇 id/type/hash（A002/A003）。
  标准见 `rules/references/quality.md`，配置事实源在 `pyproject.toml`。
- 2026-09-17 · 已定 · **代码是唯一事实，文档随代码回写**；旧概念（manifest / space / chunk / 基板 substrate /
  keyed CID）不再复活，架构文档与 `README.md` / `AGENTS.md` 已同步。
- 2026-09-19 · 已定 · **导入面必须统一、直观**：同一件事的代码收在同一个目录 / 包下、从一处可导入，
  不许散落。判据 =「外部开发者懒得研究内部，散乱就导入不了，只会骂作者」。布包时按"使用者视角"归拢。

## 目录结构（2026-09-19，重定）

- 已定 · **取消 `cairn.` 前缀**：`src/` 下直接放顶层包 `conf` / `core` / `feature` / `ui`
  （+ 实验 `net` / `server`）；导入形如 `from core.storage import Bucket`。
- 已定 · **重命名**：`core/store → core/storage`、`domains → feature`、`comm → net`；
  `cairn/types` 与 `cairn/core/types` 合并为 `core/types`。
- 已定 · **UI 源码整体移除、待重建**：其实现、测试与专用工具一并删除；`src/ui/` 暂留空壳，
  技术路线（Widgets / decl）作废、待重新立项。桌面入口 `ui.app:main` 与打包待 UI 恢复。
- 已定 · 实验顶层包 `net` / `server` 不进 hatch wheel。

## UI 技术路线（2026-09-18；2026-09-19 源码删除 / 待重新立项）

> 已废弃（2026-09-19）：以下 Widgets 宿主 + QML 岛的实现已随重定删除，仅作历史与重估参考。

- 已定 · **Widgets 宿主 + QML 岛**：工作台外壳、列表/树、检查器、编辑器、菜单/对话框全部走
  QtWidgets（Python 对象组合）；QML 只保留给**画布 / 大规模关系图 / 特殊视觉**这类自包含「岛」。
- 已定 · **编辑器用 `QTextEdit` + `QTextDocument` + `QUndoStack`**：一条硬行 ≈ 一个 block，
  与笔记行模型同构；跨行选区、撤销/重做、IME、代码高亮由框架提供（QML 逐行 `TextEdit` 做不了）。
- 已定 · **判据三条**：① Qt 只支持 Widgets 里嵌 Quick，不支持 Quick 里嵌 Widgets；
  ② App 需要的动效类别（硬切/软切/渐变/滑移）Widgets 全覆盖，QML 的连续高频场景图收益与产品不符；
  ③ **实现语言须在负责人射程内**——组件库用 Python，负责人可参与设计与维护（QML 做不到）。
- 已定 · **命名分层**：`App`（QObject 组合根：Session/facade/命令表）+ `MainWindow`（QMainWindow）
  + `Component` / `Panel` / `Page`（部件基类）。依赖显式注入，不用全局单例。
- 已定 · **QML 岛是哑视图**：输入类型化 VM、输出回调；不持应用状态、不碰 Vault、不反向耦合。
- 进行中 · 现有 QML 的 Shell / Navigator / Editor / Inspector **逐步迁到 Widgets**；
  详见 `progress.md` 的「UI 重建」。
- 已定 · 组件建造四规则：**联动在控制器**（compound components，不控件互连）、
  **布局靠 `VBox/HBox/Grid/Split` 嵌套组合**（不新增原语）、**增长只在原子与页面**、
  **主题 = 点分配置 → QSS 编译 + 有限 Qt 侧增强**。细则见 `rules/references/ui-boundary.md` §6。

## 声明式描述层 decl（2026-09-19，新增；同日源码删除 / 已废弃）

> 已废弃（2026-09-19）：`cairn.ui.decl` 实现已随 UI 删除，仅作历史与重估参考。

- 已定 · **`cairn.ui.decl` 是 UI 描述层**：语法层 `Node / Layout / Display / Page / Component`；
  **交替规则**——`Layout` 只排列（子件只能是显示节点）、`Display` 只承载 `Layout`/`Component`、
  `Page` 只能挂在 `Layout` 下且必含一个 `Layout`。信号**不是类型**，是所有节点内置的意图边
  （`on` / `emit`）。
- 已定 · **配置分两类**：`Theme`（**封闭词表**，外观唯一真源，样式只写 `token.*` 引用、禁硬编码）
  与 `UiConfAttribute`（**开放词表**，随组件继承生长，支持新增 / 覆盖 / 重定向 / 失效）。
  两者重叠用「**属性设状态、样式选状态**」的伪状态桥缝合。
- 已定 · **重定向 ≠ 失效**：重定向（改名 + 兼容别名）安全；失效会破坏「子类可当父类用」，
  慎用。防配置爆炸靠**组合 > 深继承**。
- 已定 · **`Scope` 是隔离边界**（主题 / 绑定 / 撤销 / 焦点），可派生子作用域并继承主题；
  `App` 只是最外层的 Scope + 根布局。
- 已定 · **编译层单向一次性**：描述树 → Qt 树，扩展只加 translator（注册表）；
  `Raw` 是一等逃生舱。**不造 reconciler / 不搬响应式**——响应仍走内核 → `Session` → 模型。
  旧规则「不要造绑定框架」继续有效：decl 只做描述 + 编译，无绑定框架。
- 已定 · `Layout`（排列机制）与 `Page`（语义目的地）是两类，**不可合并**；两者的子类
  即「词汇层」（`VBox/Grid/Table…`、`ListPage/DetailPage…`）。
- 已定 · **路由 / 宿主 / 生命周期**：`PageRegistry`（route → Page 工厂，注册顺序即标签序）+
  `PageHost`（即 **Tab 槽**，`QTabBar` + `QStackedWidget`）。页面控件**首次显示才构建**（懒加载）；
  切换时触发 `Page.on_enter/on_leave`。加页面 = 注册一行，不动外壳。

## UI 内核（2026-09-19，重定；设计总纲 `docs/architecture/ui-kernel.md`）

- 已定 · **两套内核**：数据内核（`core`/`feature`）升级调整；UI 内核（`ui/`）重新设计。
  **UI 内核 ≠ Qt**——它负责「对象 → 界面」的生成 / 编译 / 绑定 / 配置，Qt 只是实现材质。
- 已定 · **技术路线：QtWidgets 宿主 + QML 岛**（沿用 2026-09-18 三条判据）；画布 / 大关系图走 QML 岛。
- 已定 · **数据直通 = 内核预埋信号代理 + 投影 + 命令**：信号代理（现为 `core/events.py` 的
  `EventBus`）是 UI 与 feature 的统一变更源；UI 经 `投影(Session) → Bridge → Model` 消费，
  **不 import `feature`、不碰 `Vault`/`Bucket` 内部**；写回一律走命令。**单向数据流**。
- 已定 · **快捷创建 = 对象驱动生成**：由领域对象（Note/Project…）内省出 **UI 模板树**（可用初稿）+ 套通用架构默认行为；开发者只改细节。**特化优于通用**，不求外部框架式极致通用；自动生成只出模板，细节不猜、不假装已实现。
- 已定 · **事件绑定 = 声明 + 编译**：组件只发意图 → 命令；内核信号 → Session → Qt。**不做响应式框架 / reconciler / 双向绑定**。
- 已定 · **统一 Config = Theme（封闭词表，外观唯一真源）+ UiConf（开放词表，随组件生长）**；选择器 `widget.<类型>[:<状态>]`，**比 CSS 轻**（不做层叠 / 继承 / 优先级）。
- 已定 · **数据内核须配合补**：字段内省 API（现缺，类型信息只在 `Block.__init_subclass__` 内部消费）、
  字段 traits（纯数据展示语义）、`batch` 合并事件、`Vault` 死 API 收口。
- 已定 · **各司其职 = 领域契约**：领域对象除结构 / 事件外，另声明 UI 可消费的契约
  **`fields` / `actions` / `signals`**；UI 按契约绑定与生成。**契约是领域的事，渲染是 UI 的事**。
  契约**不得长在 `Block` 上**；字段描述符（`Attr`/`Data`）属存储机制，在内核边界内投影为中立
  `FieldSpec{名字,种类,traits}`，UI 只读 `FieldSpec`，不外泄 `Attr`/`Data`/`Block`。
- 已定 · **Bucket / Block 与 UI 正交**：`core.storage`（Bucket/Block）是存储实现，**UI 不 import、
  不复用、不感知**（UI 里出现 `bucket`/`block`/`body`/`attrs`/`checksum` 即失控）；判据=
  「新开发者要懂 UI 须先学 Bucket/Block」即失败。加架构测试断言 `ui` 不 import `core.storage`/`feature`。
- 已定 · **预埋目录**（2026-09-19，空目录）：`src/core/signal/`（Qt-free 信号原语）、`src/ui/core/`（UI 内核）；
  现役 `EventBus` 是过渡，将来建在 `signal` 上。
- 已定 · **验收指标**：加领域字段 = 领域一处（+traits），UI **0~1 处**；加标准动作 = 契约一处。
  加字段仍要改 5 个 UI 文件 = 设计失败。
- 已定 · **代理是必然的（内核在变，UI 不变）**：内核随业务 / 数据变，UI 可不变，靠**代理**挡住。
  **两端各一代理**：数据侧 `core.signal.Signal`（包内核、稳定面 + 取实体操作入口）；UI 侧同构代理
  （对接 Qt 信号槽）。**`Bind` 把两个稳定面接起来**——绑定对象因此必然存在。`Signal` **不生成页面**
  （生成页面是 `Facet` 的事）。
- 已定 · **交付单元 = `Facet`**（原 `Page` 生成器含义弃用，`Page` 退为内层页面层）：一个域的整套
  UI 定义（布局 + 部件 + 绑定），由领域对象生成；`Facet(Note)` / `class NoteFacet(Facet)` 同树。
  交付：**直接交给 App（组合根）**，由 App 编译 / 挂载 / 接信号（定义被动，外部发起）。
  `Facet.__init__` **只声明两件事：属性配置 + 绑定**。
- 已定 · **绑定模型**：`bind = Bind(self)`（作用域 = Facet，随生命周期释放）；
  `bind.add(源, 目标)`：源为 UI 信号（**明确到信号**，如 `self.save_btn.clicked`），目标为
  领域 `Signal`（`self.note.favorite`）或本类方法（`self.on_clear`）——UI→内核 与 UI→UI 同写法；
  参数沿 source→target 传；**编译期校验**信号名 / 签名。Qt 物理事件与控件事件由 UI 侧代理
  **统一包成 `Signal`**，作者不碰 `QEvent`。
- 已定 · **总目标（唯一尺度）**：**更便捷、更快、更轻量、更少工作量**。
- 已定 · **`core/signal` = 现有 `EventBus` 升级，不重造**：分两层——**存储事件**（已有
  `ObjectPut`/`ObjectDeleted`）+ **语义信号**（各域声明"会喊哪些话 / 关心哪些话"，
  `emit(名字,数据)` / `subscribe(名字,处理)`）。域间**不 import、只认信号**；听了**重新读**当前状态
  （不缓存假设，解"邻居突变"）；通知非命令；处理器不可重入。`Signal(Note)` = 域的信号 / 动作句柄。
- 已定 · **`Facet` 自包含规则**：主题等内置属性**自带**；布局 / 部件**不自包含**——自己 import、选、
  配好（专属配置在对象自身）再放进去。**`set` = 设形态**（`layout.set(Grid)`）、
  **`add` = 加持有**（`layout.add((1,2),Editor)`），**语义不可混**。产物 = **对象本身直接交 App**
  （`Facet` / 包装对象；**不序列化、不加中间格式，是啥传啥**）。
- 已定 · **Config = JSON**：顶层 `token {…}`（全局外观）+ 具体配置（`note.<…> = 值` / `note.<…> {}`）；
  App 认识所有 `Facet` → **自动生成 JSON schema**（键自动列出、可校验）；**布局参数也在其中**
  （拖布局 = 改文件，不动代码）。
- 已定 · **QML 岛 = 组件化增强**（非完整 UI、非外壳）：画布 / 大关系图等**特定领域增强组件**，
  按普通原子处理——包一层 `QQuickWidget`，对外"配置进 / 信号出"，**接法同普通部件**。
- 已定 · **字段显示属性固定四词**：`label` / `group` / `display` / `editable`；**能按类型推的不写**，
  领域顺手挂、UI 照做。
- 已定 · **多页面 = `Facet` 里的 `Page`**：`Page` = 单页（布局 + 部件 + 绑定），是导航目标；
  `Facet` 持多 `Page` 并声明怎么切（`tabs`/`stack`/主从，默认 `tabs`）；**单页域不显式写页**
  （`Facet` 即默认页）；宿主由 App 给、页面懒加载、切换触发 `on_enter`/`on_leave`。
- 已定 · **字段从领域对象分析而来、不写死**；`label`/`group`/`display`/`editable` 只是**可选显示提示槽位**，
  值随领域；**信号**告知"它现在有哪些字段"。
- 进行中 · 分阶段 M0 地基 → M1 外壳 → M2 生成 → M3 扩展；每阶段以 note 打穿闭环。
- 已定 · 本设计**预期与现有 UI 规则冲突**（`ui-boundary.md` / `ui-theme.md` / AGENTS 红线），
  届时以本方向为准定向改规则。

## 通信主干 = 统一调用总线（2026-09-19，方向定）

> 取代旧口径「通知非命令」（`ui-kernel.md` §3.1.1，待回写）。

- 已定 · **定性**：这不是「事件总线 / 通知」，是**进程内统一调用主干（对象寻址空间）**。
  单进程、函数级、同步，无网络 / 无投递保证 / 无 ack；「通知」塌缩为命令，差别只剩**单播 / 多播**。
- 已定 · **三向通信同一机制**：内核↔内核、领域↔领域/内核、UI↔（内核+领域）。
  边界=**跨内核 / 跨域 / 跨 UI 才上主干**，域内正常函数调用不上（否则退化为动态消息系统，mypy 报废）。
- 已定 · **寻址零字符串、静态声明树**：`Signal.<ns>.<Domain>` 属性访问拿地址；
  动作侧也是**句柄对象**（`Signal.feature.Note.save`），不是字符串。树须静态声明，否则 IDE / mypy 全失。
- 已定 · **树节点 = 域服务单例**（处理器级对象，数量少、以单例为核心）；数据实例不进树，
  动作以目标 id 作参数（形态 A 为主；实例代理 B 仅作 UI 便利糖）。
- 已定 · **旧字符串命名信号层已移除**（`core/signal` 的 `SignalBus` / `SignalEvent` / `check_name`
  与 `Vault.signals`、其测试）：与零字符串地址树冲突，清了地面再建新主干。
- 已定 · **失败 / 返回**：进程内、Python 直接抛。命令通道**不得吞异常**
  （现 `EventBus.emit` 吞异常，`events.py:104`，须拆）：命令透传、多播才谈隔离。
- 已定 · **单例作用域 = 每 App / Vault 一个**，不做模块级全局（测试隔离，非并发考量）。
- 已定 · **UI 红线**：UI 只发命令 + 只收事件，不允许经主干点对点直调域对象内部。
- 已定 · 多播（邮件型）接收者抛异常**隔离继续**（沿用 `EventBus` 语义）；单播命令异常**透传**。
- 已定 · 树根名 **`Signal`**（旧字符串信号类已删，无冲突）；命名空间 `core` / `feature`。

### 实现（2026-09-19，已落地）

- `core/signal`：`Signal`（主干 + 地址树）/ `Domain`（域服务基类）/ `@action`（单播动作描述符）/
  `Topic`（多播信号描述符）/ `Action` / `BoundTopic`。单播经 `invoke`（异常透传），多播复用
  `EventBus`（异常隔离）。零字符串：`signal.feature.Note.save(...)`。
- **不做动态注册 / 内省**：域容器由**组合根静态声明**（`class Feature: Note: Note`），`signal.feature = feature`
  普通赋值挂上；`Domain.bind(signal)` 显式绑总线。删掉了 `Namespace.__getattr__` / `Signal.register` / 字符串 setattr
  ——动态注册**无人受益**（所有使用方都静态知道领域名），属过早泛化。
- **未绑定的域**：动作退回直接调用（便于单测与内部自调用）；`bus` 属性报「未绑定总线」。
- 作用域每 `Signal` 一实例；域容器按层静态挂载（`core` / `feature`）。

## 领域服务 / 数据分离（2026-09-19，方向定 + 已落地）

- 已定 · 领域拆两层：**`Note` = 域服务（单例；机制 / 策略，类比 `sys`）**
  + **`NoteData(Block)` = 纯数据**。
- 已定 · 数据由 **Bucket 与域服务共同管理、各管各的**：Bucket 管存储
  （oid / checksum / 内容池 / 目录 / 事件），域服务管语义（创建 / 读写 / 版本 / 关系 / 策略）。
- 已定 · 落地：`NoteData` 保留字段 + 纯内容操作（set_text / 行级 / 样式 / 段落 / blocks / references）；
  `Note` 提供 `create` / `load` / `list_notes` / `save` / `persist` / `update` / `history` / `body_at` /
  `restore` / `link` / `add_canvas` / `add_access`，并声明 `changed` 多播。版本基线 `_saved_state` 随数据。
- 已定 · 其余领域（Project / Canvas / Group …）尚未拆，按同一口径推进。

## 数据库重构（2026-09-19，方向定 / 待落地）

- 已定 · **现状 8 张表**：内核 `packs` / `contents` / `blocks` / `meta`；按需 `search` / `versions` /
   `version_heads` / `relations`。问题：无「表政策」，可派生冗余（`version_heads`）与内容副本（`search`）。
- 已定 · **`block` = 物理事实表**：`oid`（+ 至多相对物理地址）、`type`（**整数枚举**，非字符串）、
  `body_id`（→ body 池）、`size`、`created` / `updated`，外加**块自身数据 / 配置**（对象携带的字段
  序列化在一起，不再拆 `author` / `config` / `meta` 多列）。
- 已定 · **block 层不去重**（无意义）；去重在 **body 层**：body 以**哈希**为 id，同内容只存一份；
  `block.body_id` 引用 body。
- 已定 · 载体文件**随机哈希命名**（`[0-9a-z]` 的 32 / 64 位），废弃顺序 / 语义命名（`000001.pack`）。
- 已定 · **body 表保留原表名**，只把字段改成自解释（键列明确为 `body_id`）。
- 已定 · **域表不复制块内数据**：note 自身配置 / 属性已在块里，域表再存一份 = 重复 + 一致性地狱。
  域表只放**关系 / 组织**。
- 已定 · **多对多关系走独立边表**（一列塞不下）；边表**跨域共享**（note / project / group 都用），
  加 **`domain`（领域类型）** 字段区分归属。
- 已定 · **组仍是块**（`cairn.group`，实体真源，管嵌套 `group: list[str]`）。**不另建组索引表**：
  `block.type` 整数码 + `idx_block_type` 索引本身就是领域枚举——`Group.list` = `block WHERE type=group`，
  无需双写、无一致性问题。
- 已定 · **表名规范：单数、直白**。候选：`block` / `body` / `note` / `project` / `group` /
  `group_index` / `relation` / `version` / `search`。现名 `contents`（概念是 body 池，**不叫 body**）、
  `blocks`、`relations` 等改为直白名。
- 已定 · **不建 `note` / `project` 领域表**（推翻早先「每域一张表」）：其诉求已分别由
  ① `block.type` 整数码索引（枚举 / 计数）、② 跨域 `relation` 边表（关系）、③ `cairn.group` 块（分组）
  满足；再建域表只会复制块内数据，违反上条「域表不复制块内数据」。域表仅在确需「不重复块数据的
  可查询面」时才建（当前无此需求）。
- 已定 · 全局搜索保留，但**不用纯字符串全库扫**（易拖垮库）；方向 = **混合搜索**（向量 + 全文 / 精确），
  实现待定。
- 已定 · **笔记本身不去重**；去重**只在 body 层**（`body.id` = 哈希，作去重键；库里那一行只为
  「哈希 → 物理位置」）。域表 `id` 用于**引用**，稳定，不承担去重。
- 已定 · **原则**：数据库只放「要定位 / 要引用 / 要去重 / 要查」的东西；**内容本体在 pack，不在库**。
  body 行在库纯为去重索引。
- 已定 · **版本**：先留库（`version` 表即可，去掉可派生的 `version_heads`）；**版本膨胀是后续升级问题**，
  届时可专门出「版本块 / version block」外置。现在不阻塞。
- 已定 · 表名按单数直白规范：`block` / `body` / `packs` / `meta` / `note` / `project` / `group` /
  `group_index` / `relation` / `version` / `search`。
- 已定 · **迁移策略**：`catalog_version` + **增量迁移**（开发期可手跑 SQL；每次改 schema 递增版本并写迁移步骤）。
  表分两类：**真源表**（`body` 位置索引 / `relation` 边 / `version` 链）需真迁移；**投影表**
  （`note` / `project` / `group_index` / `search`）可 **drop + 从 block 重建**。
- 已定 · **长期方向**：让权威数据尽量落 **block**，DB 退为**可重建的索引 / 投影**——届时迁移 ≈ 重建索引。
  前置：版本外置为「版本块」、关系内嵌进块（`relation` 退为投影）；代价是双写。
- 待定 · `search` 是否并入投影 / FTS5 / 向量库（混合搜索实现待定）。
- 待定 · `type` 枚举码表 = kind ↔ int 的**稳定映射**（不可重编号）；倾向由各块子类自报 `code`、
  码表登记在 `core/storage`，core 不硬编码领域名。

## UI 内核修正（2026-09-19，Facet 分析 ≠ 领域契约）

> 对齐 `ui-kernel.md` §4「对象驱动生成」；修正上一轮"撤销"过头。

- 已定 · **撤销的是「领域额外写契约」**（要求每个领域先声明一份 fields/actions/signals 清单），
  **不是**对象驱动生成本身。领域**无需额外作者化**——它的"契约"就是对象自身已有的声明：
  字段（`Attr`/`Data` 注解）、动作（`@action`）、信号（`Topic`）。
- 已定 · **`Facet` = 分析器 + 组织器 + 包装器 三合一**，是整套体系里**最重**的一环，其余皆辅助。
  交付 = 一个完整的**领域 UI**：页面 / 组织 / 布局 / 组件 + 信号绑定 + 路由配置；最终交给 `App` 注入，
  并告知"这块 UI 放哪 / 怎么嵌"，由 App 生成整套页面。
- 已定 · **分析是浅的、确定性的**（达不到代码生成器级，只做确定性动作）；**确定性来自定义位置**——
  **全部写在 `Facet.__init__`**：`self.xxx = …`（属性配置）、`.add(...)`（组织 / 布局 / 组件）、
  `.bind(...)`（绑定）、`.navigate(...)`（路由）。**这份 `__init__` 内容天然就是该 UI 的契约与约定**，
  实例化即成立；后续代码只在其上影响计算与生成，不做运行时推断。
- 已定 · **`Facet` 声明 API（简化为两条）**：
  - **页面**：`self.page(page, route_signal)`——页面对象 + 路由信号，一个 API。页面切换就是"注册页面 + 用哪个信号切过去"，无更复杂机制。
  - **绑定**：`self.bind.add(source, target)`——`self.bind` 是 Facet 持有的**登记处对象**（名词），随 Facet 生命周期释放；
    `source` = UI 信号（明确到信号），`target` = 领域动作（`self.note.favorite`）或本类方法（`self.on_clear`），同一种写法。
    不用裸 `Bind()`（无主、泄漏）、不用动词式 `self.bind(...)`（无法带 `when` / 转换参数）。
- 已定 · **`Facet` 配置 API**：`self.conf.theme.set(点分路径, 值)` / `self.conf.<域|组件>.set(键, 值)`——
  **单点赋值**，清晰、可 schema 校验、不链式；`self.conf.theme = …` 只用于**整体替换**（少用）。
  `theme` = 封闭词表（外观令牌，唯一真源，组件只引用 `token.*`、禁硬编码）；
  `attr` / `ui` = 开放词表（组件 / 页面行为配置，Facet 主要在此 `set`）。
- 已定 · 配置不止 `set`，**`add` 同样要有**（属性可加、样式可加）。底层 Qt 支持动态样式：
  QSS 可全局 / 逐控件追加并 `unpolish`/`polish` 重算；动态属性选择器可做状态驱动。
  `set` = 覆盖已有键；`add` = 新增键 / 规则（**须过 schema**，不得破坏封闭词表）。
- 已定 · **配置 = 一株有向路径树**：绝对路径 `app.<域>.<page>.<layout>.<com>…:<item> = 值`（嵌套多深链就多长，
  **超长无妨，求确定性**）；`{}` 写多项，`:item = 值` 为 CSS 式高级写法。
  - **两个面、一套词汇**：Facet 代码面 `self.conf.<组>.set(局部路径, 值)`；文件面写绝对路径，编译后同一套。
  - **App 持有 schema**（由 Facet 树自动生成），统一获取 / 计算；IDE 据此校验路径。
  - 同一路径下 `attr` 自由、`theme` 只认词表令牌项。
  - 副产品：**路径 = 布局结构** → 改配置即改布局，未来 `CairnThemeTools` 可据此做可视化布局（对应 `ui-kernel` §6「拖布局 = 改文件」）。
- 待定 · 配置的第三式 `bind`（样式随状态 / 信号变）：技术可行，但与事件绑定 `Bind` **撞名**，
  建议改名 `when` / `state`；状态样式需 repolish，按 `ui-boundary`「逐条加、可测、有边界」推进。
- 已定 · 字段不写死：由**内核提供中立内省**（对象结构 → 中性视图；UI 不 import `core.storage`），
  `Facet` 读它生成；`label` / `group` / `display` / `editable` 只是可选显示提示槽位。
- 已定 · **领域在组合根硬标注，不做运行时推导 / 稳定代理**：领域数量少（≤10）且确定，不像插件那样不可预知，
  直接在组合根显式 `signal.register(Note)`、写死 `note` / `project` 即可。`Signal` 的命名空间机制保持通用，
  但**不做内省 / 推导**；**领域契约 / 从插件推导 UI 只在未来引入插件系统时再上**（届时基于本底层）。
- 可选 · **地址树静态声明**（IDE 友好）：`signal.feature.Note` 目前是动态 `__getattr__`，IDE 不补全；
  若需要，可在组合根层**静态声明**命名空间属性 + 类型（领域少、代价低）。非必须。
- 已定 · **红线不动**：`Facet` 收的是**注入进来的领域对象**，自己不创建，故**无需 import `feature`**
  （类型提示可选，`object` / 鸭子类型即可）；"UI 不 import `feature` / 不碰 `Vault`" 继续有效。
  真正认识领域的只有**组合根**（创建服务并注入），不在 UI 内。
