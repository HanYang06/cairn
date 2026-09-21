<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# L0 · 存储层规格（Storage）

> Cairn 的最底层：一个本地优先、内容寻址的**桶 + 块**存储。
> 本文件是 **L0 的唯一事实来源**；上层（领域模型、服务、UI）建立在它之上。
> 跨层的**数据结构总纲**见 [`data-model.md`](./data-model.md)。
> 访问策略 / 密钥分发 / P2P 见 [`access.md`](./access.md)（本地不加密，见 §7）。

状态：**草案 v2.0**（2026-09-16 重写：桶 / 块 / 目录；删除加密与清单）

---

## 1. 定位与设计公理

存储层只有两个概念：

1. **桶（Bucket）**——一个受管的**文件系统**，是**类**不是数据结构；只管配置与方法。
2. **块（Block）**——唯一被存进桶的东西，形如 `{id, checksum, type, body, attrs, ...}`。

公理：

- 上层的一切（笔记 / 资产 / 项目 / 画板 / 索引 / 变更）**最终都是块**或其属性；
  区别只在 `type` 与 `body`，不再另开"存储物种"。
- **本地不加密**，落盘明文；加密只用于传输 / 服务端（见 §7）。
- 内容按 `checksum`（= `body_hash`）**内容寻址**；桶在 **`body` 表**按该哈希去重（同 body 只存一份）。
  分片 / 索引块（`part` / `index`）不做块级去重；`block.type` 为**整数码**（`block_type` 表）。
- 没有 manifest、没有 space、没有分块池：这些概念已删除。

### 非目标

- 不定义"笔记"内部结构（L3，见 [`note-model.md`](./note-model.md)）。
- 不定义网络传输 / 发现（见 [`access.md`](./access.md)）。

---

## 2. 词汇表

| 术语 | 含义 |
|---|---|
| **桶 Bucket** | 受管文件系统：管 `packs/` 与 `catalog.db`；类，不是数据结构 |
| **载体 Pack** | 一个追加写的文件，装很多块；写满即封口 |
| **块 Block** | 存储单元；`id`(稳定 OID) + `checksum`(内容哈希) + `type` + `body` + `attrs` |
| **目录 Catalog** | SQLite：块 → 物理位置的**唯一真源**；另有 versions / relations / search 等表 |
| **OID** | 块身份，ULID（26 字符 Crockford Base32） |
| **checksum** | 内容哈希，BLAKE3 十六进制串 |
| **Config** | 块的写入配置（如 `isolated` 独占载体） |
| **Attr** | 块的描述字段描述符；`Attr(item=)` 可类型化列表元素。字段由**领域**声明（`Block` 不带业务字段） |

> **哈希是字符串**：`id` 是 ULID 字符串，`checksum` 是十六进制字符串——便于进 CBOR/JSON、
> 比较与建索引，不需要二进制哈希对象。

---

## 3. 目录布局

```
<bucket>/
  catalog.db            # 目录（唯一真源）：块位置 + 版本 + 关系 + 检索
  packs/                # 载体文件，平铺、**随机哈希命名**
    3f9a…（[0-9a-z] 32 位）
```

- pack 名是**随机哈希**（无语义 / 无顺序号）；内容按 checksum 去重，逻辑块另有稳定 id。
- 没有 `.cairn/` 派生索引、没有 `db/structure.db` 之分：**只剩一个目录库**。

---

## 4. 块（Block）

```python
Block:
  id          # 稳定身份（ULID），创建即分配，**锁死**
  checksum    # = body_hash：只覆盖 body（BLAKE3，十六进制）；桶按它去重
  type        # 承载类型（str / Enum）
  body        # 主体（list / bytes / 标量）→ 进**内容池**，按 body_hash 去重
  attrs       # 原生属性（dict）→ 随块行存，**不参与去重**
  config      # 写入配置（dict）
  author      # 作者
  size        # 主体字节数（bytes 取长度，其余取确定性编码长度）
  created / updated   # unix ms
```

- **body 与 attrs 分家**：`body` 进内容池（同 body 只存一份）；`attrs` 随块行存。
  于是「同正文、不同属性（标题 / 标签 / 签名 / 时间）」既能共享正文、又互不污染。
- `checksum`（= body_hash）只算 body，不含 id / attrs / 签名；子类可覆写口径
  （笔记剥离行 id、把行内样式算入）。
- 领域结构**直接继承 `Block`**，用 `Attr` / `Body` 重新描述字段；`Bucket` 负责 I/O。

---

## 5. 载体（Pack）

- 追加写；写满（`pack_max_blocks` 或 `pack_max_bytes`）即封口，换下一个。
- 块在 pack 里就是编码后的**内容字节**，靠目录的 `(pack_id, offset, length)` 定位。
- 不追求 pack 自描述：目录是唯一真源（丢目录即失联，这是明确取舍）。
- `config["isolated"] = True` 的块**独占一个载体**，写完即封口。

---

## 6. 目录（Catalog，SQLite）

```sql
packs(id PK, name, blocks, bytes, sealed, created)   -- name = 随机哈希
body(body_id PK, pack_id, offset, length)            -- body 池：按 body_hash 去重
block_type(code PK, name)                            -- 类型码表：kind ↔ int（稳定、不复用）
block(oid PK, body_id, type, size, data, created, updated)
                                                     -- body_id=body_hash；type=整数码；
                                                     -- data=canonical({attrs, config, author})
version(id PK, oid, prev, at, payload)              -- 版本链（反向补丁；见 §9；无 heads 表）
relation(id PK, src, dst, kind, domain, at, attrs, created)
                                                     -- 关系（一等行；domain=归属领域）
search(oid PK, body)                                -- 检索文本
meta(key PK, value)
```

- `body` 就是**去重池**：`body_id`（主键）→ 物理位置，查找 O(1)；同 body 只存一份。
- `block.data` 一次性装 `{attrs, config, author}`（不再拆多列）；`block.type` 为整数码。
- 目录是**唯一真源**：块的位置只在这里；不做"可重建的派生索引"。
- 领域自描述的业务表走 `Block.tables()` + `Bucket.mount()` 创建；通用查询用 `Bucket.table()`，
  复杂 SQL 走 `Bucket.execute()/query()`——上层不 import sqlite。

---

## 7. 加密（本地不做）

- **落盘明文**。加密只用于**传输 / 服务端**（详见 [`access.md`](./access.md)）。
- 理由：本地优先、单机单写者；本地加密的收益与代价不成比例（见记忆决策）。
- 因此 `checksum` 直接用明文哈希；去重没有任何密钥域的冲突。

---

## 8. 写入 / 读取流程

写入（一次 `bucket.put(block)`）：

1. `block.validate()`（领域校验，默认放行）；
2. 算 `body_hash`；查 body 池，无则：`canonical(body)` → 追加到活跃 pack（`fsync`）→ 记 `body`；
3. 记/更新 `block` 行（`body_id=body_hash`，`type`=整数码，`data=canonical({attrs,config,author})`）；提交事务。

读取（`bucket.get(cls, id)`）：

1. 由 `block` 行拿 `body_id` → `body` 定位 → 读 pack 得 body；`data` 取 attrs/config/author；
2. 拼合还原为对应子类，重算 `body_hash` 校验；类型不符抛 `KindMismatchError`。

大内容：`Bucket.put_content(bytes)` 切片 + 索引块（`index`）；分片块不做块级去重。

---

## 9. 版本（通用引擎 `VersionStore`）

- 引擎在 `core/storage/version.py`，**block 亲和**：以块 id 为键，只管链、顺序、回放、压实，
  不认识领域语义；域提供 `Codec`（`digest / diff / apply`）。
- 表 `version(id PK, oid, prev, at, payload)`（**无 `version_heads`**；头 / 计数由表推导）：
  - **版本 id = `blake3(canonical({prev, at, sig}))`**：哈希身份 + `prev` 单亲链；`head` = 不被任何
    `prev` 指向者，沿 `prev` 走，不依赖时间/序号（Git 式，将来可扩多亲 DAG）。
  - 第一版记一个**根节点**（空补丁），此后每次内容变化追加一个反向补丁。
- 补丁是**反向的**（新 → 旧）：当前版本永远在块里，历史从 `head` 反向回放重建。
  - 笔记补丁按**行 id** 锚定：`PUT`（载荷=旧值）/ `DROP` / `@order`；未变更行不入补丁。
- 保留窗默认 **30 天**，更新时**惰性压实**（丢链尾）。哲学：「**笔记残页**」——补丁脱离当前块
  上下文即失效；压实=永久遗忘；传输必须带 base；`fold`（把链折成新版本）尚未实现。
- 块本身**不承载版本**：版本是笔记 / 项目各自的策略（同一引擎，不同 Codec）。

---

## 10. 关系（一等 DB 行）

- 表 `relation(id, src, dst, kind, domain, at, attrs, created)`；`kind` 有 `derived-from` /
  `references` / `contains` 等；`domain` 标明边归属的领域（note / project / group …）。
- `outbound(src)` / `backlinks(dst)` 直接查表 → 引用拓扑（A→B→C）。
- 关系**不是块**（去对象化）。

---

## 11. 删除与回收

- `bucket.delete(id)` 只摘 `blocks` 行；物理内容留作空洞（可能被其它 id 共享）。
- pack 压实（收回空洞）尚未实现——列为工程债。

---

## 12. 并发与锁

- 单写者：同一进程串行；跨进程锁（`.lock`）尚未实现。
- 多读者可只读已提交内容。

---

## 13. 依赖

| 用途 | 库 |
|---|---|
| 哈希 | `blake3` |
| 序列化 | `cbor2`（确定性） |
| 目录 / 表 | stdlib `sqlite3` |
| 其余 | stdlib：`os` `pathlib` `secrets` `dataclasses` |

> 传输 / 服务端加密将来另选（须过许可关：只引 MIT/BSD/Apache，禁 GPL/AGPL）。
