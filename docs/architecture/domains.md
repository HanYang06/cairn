<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 领域扩展与日志约定

> 承接 [`storage.md`](./storage.md)（L0 桶 / 块）与 [`data-model.md`](./data-model.md)（对象模型总纲）。
> 定义领域（L3）如何扩展数据与行为，以及日志的分层约定。

状态：**草案 v0.2**（按「块基类 + 字段描述符」重写；旧 Manifest / meta.props / structure.db 表述作废）

---

## 1. 一条继承线：领域结构直接继承 `Block`

| | 载体 | 关系 |
|---|---|---|
| 结构基座 | `Block`（`core/storage/block.py`） | **固定**，领域不新增顶层字段 |
| 领域结构 | 子类用 `Attr` / `Data` / `Body` 重新描述字段 | **可继承**，注册表按 `type` 分发 |

- 领域类**没有中间层**，`Note` / `Asset` / `Project` / `Canvas` 都直接 `class X(Block)`。
- 扩展方式只有两种：**加一个 `type` 子类**、或**给已有类加字段**（字段落在块的 `attrs` / `body`，不碰 `Block` 的硬件字段）。
- **不新增块顶层字段**：`id` / `checksum` / `type` / `body` / `attrs` / `config` / `author` / `size` / `created` / `updated`
  是硬件面，领域只重描述 `body` 与 `attrs`。这样确定性 CBOR 编码与 `checksum` 口径始终稳。

> 早期文档里的 `Manifest` / `meta` / `meta.props` 已废弃：不存在"清单"这种对象，
> 描述性字段就是块的 `attrs`（见 [`storage.md`](./storage.md) §4）。

---

## 2. 类型命名与字段

### 2.1 `type` 必须命名空间化

约定 `cairn.<domain>.<kind>`：

- 官方：`cairn.note`、`cairn.canvas`、`cairn.asset`、`cairn.project`、`cairn.group`、`cairn.block`（裸块兜底）。
- 内部：`cairn.part` / `cairn.index`（大内容分片与索引块，见 `storage.md` §8）。
- 第三方用自有前缀（如 `io.example.*`）；`cairn.*` 保留给官方。

定义 `type` 的子类会**自动登记**进 `Block._REGISTRY`（`Block.__init_subclass__`），
`Block.decode` 据此还原成正确子类；未知 `type` 退回裸 `Block`。用 `known_kinds()` 列出现有类型。

### 2.2 字段两种写法

`id` / `checksum` 之外的字段用**描述符**声明，落在 `attrs` 上：

```python
class Note(Block):
    type = "cairn.note"
    schema: Attr[int] = 1  # 注解即类型、右边即默认值
    title: Attr[str | None] = None
    tags: Attr = Attr(factory=dict, coerce=normalize_tags)  # 显式描述符
    canvas: list[str] = []  # 裸容器注解自证 → Data 字段
    body: NoteBody = NoteBody()  # 结构化 body，每实例一份
```

| 描述符 | 语义 | 存储 |
|---|---|---|
| **`Attr`** | **属性**（标题 / 标签 / 签名等描述性元数据） | 块的 `attrs` |
| **`Data`** | **数据**（画板 / 多媒体等承载内容；与 `Attr` 同机制） | 块的 `attrs` |
| **`Body` / `BodyField`** | 主体内容，进**内容池**按 `body.hash` 去重 | 块的 `body` |

- `Attr(item=Type)`：列表 / 值字段类型化——存储是紧凑数据，取出来是类型化对象（需 `to_data` / `from_data`）。
- `schema`：领域自己的结构版本（int），读取到未知版本应拒绝而非静默降级。
- 字详细则（注解即类型、`coerce`、`Data` 免标记）见 [`storage.md`](./storage.md) §4 与 `core/storage/block.py`。

### 2.3 内容 vs 描述 vs 结构

| 容器 | 放什么 | 特征 |
|---|---|---|
| **body**（内容池） | 正文行序列、画板数值、二进制本体 | 按 `body_hash` 去重；同 body 只存一份 |
| **attrs** | `title` / `tags` / `signature` / `props` / `schema` | 随块行存，**不参与去重** |
| **DB 表** | 关系（`relations`）、领域自描述业务表 | 可查询 / join，**不是块** |

红线：

- **内容进 body**（走内容池），描述进 attrs，**关系进 DB**；不要再为"统一"把关系包成块。
- 也不再要求"结构数据全部进 DB"：标签 / 属性本就是块字段，只有**关系**是独立 DB 行。

---

## 3. 领域契约

```python
class Block:
    type: str  # cairn.<domain>.<kind>

    @classmethod
    def tables(cls) -> dict[str, dict[str, str]]: ...  # 领域自描述的业务表
    @classmethod
    def bind(cls, bucket) -> None: ...  # 挂载：建表 / 关联动作（默认建 tables）
    def validate(self) -> None: ...  # 写入前校验，默认放行
```

- **注册表**：`type -> 子类`（`Block._REGISTRY`）；`Bucket.put` 时 `mount(type(block))` 触发 `bind`。
- **业务表**：领域用 `tables()` 声明表结构，桶用 `Bucket.mount()` 幂等创建；
  通用查询用 `Bucket.table()`，复杂 SQL 走 `Bucket.execute()` / `query()`——**上层不 import sqlite**。
- 领域之间**互不依赖**，只依赖 core 公共 API（跨域引用走 `Relation` 或延迟导入，如 `note.link`）。
- 关系领域（`feature/relation.py`）特殊：它是**一等 DB 行**，不是 `Block` 子类；
  `src` / `dst` / `kind` / `at` / `attrs` 直接落 `relations` 表（见 `storage.md` §10）。

---

## 4. 领域 schema 版本

- 每个领域类带 `schema: Attr[int]`（int），跟块一起落盘。
- 迁移在**读取 / 升级**时进行：比较 `schema`，就地转换字段后写回（内容变了才产生版本，见 `storage.md` §9）。
- 读到未知 / 过高版本：拒绝并报错，**不静默降级**。

---

## 5. 大内容：交给桶的分片

- 资产 / 大正文不自己做分片：`Bucket.put_content(bytes)` 小则一块、大则切片 + 索引块
  （`cairn.part` / `cairn.index`），返回一个可引用的稳定 `id`（见 `storage.md` §8）。
- 分片块**不做块级去重**（`_NO_BLOCK_DEDUP`）；去重只发生在领域对象这一层。

---

## 6. 日志：诊断 vs 活动（两层，互不混淆）

### 6.1 诊断日志（自带，全库统一）

- core 只用 `logging.getLogger(__name__)` 发事件，**绝不配置** handler / level / 格式。
- 命名空间天然分层、天然隔离：

```
core
  └─ storage                  # L0
feature
  ├─ note                     # 各领域独立
  └─ project
ui
```

- **配置在应用层**（UI 启动时）：按命名空间把各域路由到各自的 handler / 文件，互不混杂。库自身不设默认输出。
- 默认策略建议：`core` / `feature` 根 WARNING；开发用 DEBUG / INFO。

### 6.2 活动 / 审计日志（领域自有，持久化）

- 这是**数据，不是 logging**：是持久化、可（选择）加密的事件记录，落在**块桶**里。
- **各领域一套独立 schema，绝不混存**：
  - 项目：`cairn.project.*` 自己的事件类型。
  - 博客 / 帖子：`cairn.blog.*` 自己的事件类型。
- 每个领域的事件 = 普通块（`type = cairn.<domain>.event.<name>`）。
- 未来 P2P 可选的同步 / 审计轨迹，也建立在这一层，而非诊断日志。

---

## 7. 待定

1. `tables()` / `bind()` 的发现机制（内置注册 vs 入口点插件）。
2. 领域事件 schema 与保留策略。
3. 应用层日志配置是否暴露给用户（级别、文件轮转）。
