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
- 已定 · **Body 是容器基类**（`core/store/block.py`）：无 ID、依存于块；自带状态字段 `hash`
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
