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
- 内容按 `checksum` **内容寻址**；去重发生在**领域层**（note 只与 note 比），不跨领域。
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
| **Attr** | 块的原生属性（含 `title/tags/...`）；`Attr(item=)` 可类型化列表元素 |

> **哈希是字符串**：`id` 是 ULID 字符串，`checksum` 是十六进制字符串——便于进 CBOR/JSON、
> 比较与建索引，不需要二进制哈希对象。

---

## 3. 目录布局

```
<bucket>/
  catalog.db            # 目录（唯一真源）：块位置 + 版本 + 关系 + 检索
  packs/                # 载体文件，平铺、顺序命名
    000000.pack …
```

- pack 名不含任何明文，只是顺序号；内容按 checksum 去重，逻辑块另有稳定 id。
- 没有 `.cairn/` 派生索引、没有 `db/structure.db` 之分：**只剩一个目录库**。

---

## 4. 块（Block）

```python
Block:
  id          # 稳定身份（ULID），创建即分配，**锁死**
  checksum    # = BLAKE3(canonical(type, body, attrs))，十六进制
  type        # 承载类型（str / Enum）
  body        # 主体（list / bytes / 标量）
  attrs       # 原生属性（dict）
  config      # 写入配置（dict）
  author      # 作者
  size        # 主体字节数（bytes 取长度，其余取确定性编码长度）
  created / updated   # unix ms
```

- `content()` = `{type, body, attrs}`；`checksum` 只覆盖它。
- `encode()` 落盘时不含 `id`：**内容按 checksum 去重**，身份由目录行记录。
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
packs(id PK, blocks, bytes, sealed, created)
contents(checksum PK, pack_id, offset, length)      -- 物理内容，按 checksum 去重
blocks(id PK, checksum, type, size, author, config, created, updated)  -- 逻辑块
versions(id PK, oid, seq, at, diff)                 -- 笔记版本（增量 diff）
relations(id PK, src, dst, kind, at, attrs, created)-- 关系（一等行）
search(oid PK, body)                                -- 检索文本
meta(key PK, value)
```

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
2. 算 `checksum`；领域对象按 checksum 查是否已有物理内容，无则：
   编码 → 追加到活跃 pack（`fsync`）→ 记 `contents`；
3. 记/更新 `blocks` 行；提交事务。

读取（`bucket.get(cls, id)`）：

1. 由 `blocks` 行拿 checksum → `contents` 定位 → 读 pack；
2. 解码为对应子类，重算 checksum 校验；类型不符抛 `KindMismatchError`。

大内容：`Bucket.put_content(bytes)` 切片 + 索引块（`cairn.index`）；分片块不做块级去重。

---

## 9. 版本（笔记，增量 diff）

- 表 `versions(oid, seq, at, diff)`；每条 diff 描述"从新版回上一版"的最小单段改动：
  `{i, off, del, ins}`（元素下标 / 字符偏移 / 删除长度 / 插入内容）。
- 当前版本永远在块里；历史按 diff 反向回放重建（`body_at(seq)`）。
- 保留窗默认 **30 天**，更新时**惰性压实**（过期 diff 丢弃）。详见 `note/versions.py`。
- 块本身**不承载版本**：版本是笔记 / 项目各自的策略。

---

## 10. 关系（一等 DB 行）

- 表 `relations(id, src, dst, kind, at, attrs, created)`；`kind` 有 `derived-from` /
  `references` / `contains` 等。
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
