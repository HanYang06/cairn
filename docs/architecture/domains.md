<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 领域扩展与日志约定

> 承接 [`storage.md`](./storage.md)（L0 固定基座）。定义领域(L3)如何扩展数据与行为，以及日志的分层约定。

状态：**草案 v0.1**

---

## 1. 两条"继承"线：数据固定，行为继承

| | 数据基座 | 行为基座 |
|---|---|---|
| 载体 | `Manifest`（存储结构） | `DomainObject`（领域类） |
| 关系 | **固定**，不可被领域继承 | **可继承**，类似 `nn.Module` |
| 扩展方式 | 通过 `type` 鉴别 + `meta` 扩展域 | 通过注册表按 `type` 分发 |

**基础一致 = 契约一致，而不是结构继承。** 领域不得往 `Manifest` 里加字段；否则确定性 CBOR 编码与签名会失稳，域概念也会倒灌进 core。

---

## 2. 类型命名与扩展域

- `type` 必须**命名空间化**：`cairn.<domain>.<kind>`
  - 例：`cairn.note`、`cairn.blog.post`、`cairn.project`、`cairn.asset.image`
  - `cairn.*` 保留给官方；第三方用自有前缀（如 `io.example.*`）。
- 扩展域固定为 `meta`：
  - 公共可索引：`meta.title`、`meta.tags`
  - 领域私有：`meta.props`（领域自定 schema）
  - 领域版本：`meta.schema`（int，见 §4）
- payload（对象字节流）由领域自定编码，core 视作不透明。

### 2.1 只有一个扩展字段，两个容器

对象在存储层的可扩展面**只有一处**：`meta`（其中 `meta.props` 放领域数据）。**不要**为每种内容新增顶层字段——那正是会失控的"结构继承"。

但必须分清两个容器，各司其职：

| 容器 | 类型 | 用途 | 约束 |
|---|---|---|---|
| **payload**（对象字节流） | 任意字节 | 多媒体、正文、大块数据 | 无上限、分块、去重 |
| **props**（`meta` 下的 CBOR map） | 结构化小数据 | 描述 / 索引字段 | 随 manifest 签名，**必须小** |

规则：**能进 payload 的绝不进 props**。props 只放"用来描述与索引"的少量字段。

领域用 dataclass 给 props 一个**类型化视图**，但落盘仍是普通 CBOR map：

```
NoteProps(dataclass) ──Handler.to_props()──▶ {"title": ..., "tags": [...], ...} (CBOR)
                     ◀─Handler.from_props()──
```

**多媒体 / 复合内容**靠"多对象 + OID 引用"，而非把一切塞进一个对象：

```
note 对象 (payload = 正文, props.attachments = [oid1, oid2])
  ├─ image 对象 oid1 (payload = 图片, 独立分块 / 去重)
  └─ video 对象 oid2
```

这样"啥都能存"由 payload 与对象组合保证，而 manifest 始终轻、始终可签名。

---

## 3. 领域契约（注册表 + 基类）

```
cairn.domains
  DomainObject            # 行为基类：包裹 (Vault, Oid, ObjectInfo)
    ├─ Note
    ├─ BlogPost
    ├─ Project
    └─ Asset

Handler 协议（每个 type 注册一个）：
  type: str
  schema_version: int
  validate(meta) -> None                 # 写入前校验
  index_rows(info) -> Iterable[Row]      # 供 SQLite 索引
  migrate(meta, from_version) -> dict    # 版本迁移
  search_text(payload) -> str | None     # 可选：供 FTS
```

- 注册表：`type -> Handler`。`Vault.put` 时按 `meta.schema` 与注册表校验。
- 领域之间互不依赖，只依赖 core 的公共 API。

---

## 4. 领域 schema 版本

- 约定存于 `meta.schema`（int，已随 manifest 签名保护，**无需改 core 结构**）。
- 迁移在**读取/升级**时进行：`Handler.migrate(meta, from_version)` → 新 `meta`，写回时 `seq+1`（版本链）。
- 读取到未知/过高版本：拒绝并报错，不静默降级。

---

## 5. 日志：诊断 vs 活动（两层，互不混淆）

### 5.1 诊断日志（自带，全库统一）

- core 只用 `logging.getLogger(__name__)` 发事件，**绝不配置** handler / level / 格式。
- 命名空间天然分层，天然隔离：

```
cairn
  ├─ core                     # L0
  ├─ domains.note             # 各领域独立
  ├─ domains.blog
  ├─ domains.project
  └─ ui
```

- **配置在应用层**（UI 启动时）：按命名空间把各域路由到各自的 handler/文件（`.cairn/logs/<domain>.log`），互不混杂。库自身不设默认输出。
- 默认策略建议：`cairn` 根 WARNING；开发用 DEBUG/INFO。

### 5.2 活动 / 审计日志（领域自有，持久化）

- 这是**数据，不是 logging**：是持久化、可（选择）加密的事件记录，落在对象池里。
- **各领域一套独立 schema，绝不混存**：
  - 博客/帖子：`cairn.blog.*` 自己的事件类型与空间。
  - 项目：`cairn.project.*` 自己的事件类型与空间。
- 每个领域的事件 = 普通对象（`type = cairn.<domain>.event.<name>`），可用独立私密空间承载。
- 未来 P2P 可选的同步/审计轨迹，也建立在这一层，而非诊断日志。

---

## 6. 待定

1. `Handler` 的发现/加载机制（内置注册 vs 入口点插件）。
2. 领域事件 schema 与保留策略。
3. 应用层日志配置是否暴露给用户（级别、文件轮转）。
