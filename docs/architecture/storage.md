<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# L0 · 存储层规格（Storage）

> Cairn 的最底层：一个本地优先、内容寻址、分块、按档位加密的对象池。
> 本文件是 **L0 的唯一事实来源**；上层（索引、领域模型、服务、UI）建立在它之上。
> 跨层的**数据结构总纲**（逻辑/内存态/存储态、基板、对象图）见 [`data-model.md`](./data-model.md)。
> 访问策略 / 密钥分发 / P2P 相关内容见 [`access.md`](./access.md)。

状态：**草案 v0.3**（并入 Space 层、签名版本链、可见性档位；结构数据迁往权威结构库）

---

## 1. 定位与设计公理

所有内容统一抽象为**不透明的二进制对象（Object）**，落入 **对象池（Pool）**；每个对象归属一个 **空间（Space）**，空间承载"可见性档位 + 加密密钥 + 去重范围"。这带来：

1. **保密**：按档位加密，落盘只有密文（公开档除外）。
2. **多模态**：对象即字节流，笔记 / 图片 / 任意文件一视同仁。
3. **去重 / 增量**：FastCDC + 内容寻址，同内容只存一份，编辑只动局部块。
4. **可演进的 P2P 基座**：块=传输单元，内容寻址=去中心寻址，空间密钥=共享粒度。

**核心公理（相对 README 的修正）：**

- 旧表述「文件是本体，SQLite 只是可重建的索引」修正为**双源**：
  - **内容真源** = `pool/` 里的 manifest / space 记录 / chunk；
  - **结构真源** = `db/structure.db`（关系 / 成员 / 标签 / 属性）——它不是派生物，**删了即丢**；
  - `.cairn/index.db` 只是内容对象的**派生索引**，可全量重建。
  - 详见 [`data-model.md`](./data-model.md) §4.2、§6.4。
- 块与清单不透明、顺序无法自证；没有 manifest，chunk 就是孤儿字节。
- **分片不等于保密**：分散只服务于去重与寻址；机密性完全由密码学提供。
- **加密是策略，不是布尔值**：按可见性档位选择密钥机制。

### 非目标

- 不定义"笔记"内部文档模型（L3）。
- 不在本文件定义网络传输 / 发现 / 同步（见 `access.md` 的预留节）。

---

## 2. 词汇表

| 术语 | 含义 |
|---|---|
| **Vault（库）** | 一个自包含目录，即一个本地对象池 |
| **Identity（身份）** | 每库一对密钥：Ed25519 签名 + X25519 密钥协商 |
| **Space（空间）** | 策略容器：可见性档位 + 空间密钥 SK + 成员 + 去重范围 |
| **Object（对象）** | 逻辑单位，稳定身份 OID，归属唯一 Space |
| **Chunk（块）** | 对象明文的字节区间，CDC 切分，以密文落盘 |
| **Manifest（清单）** | 对象元数据 + 有序块表 + 版本链；CBOR、加密、签名 |
| **OID** | Object ID，ULID（26 字符 Crockford Base32） |
| **CID** | Chunk ID，`keyed BLAKE3(space_addr_key, 明文块)` 的十六进制 |
| **MK** | Master Key，32 字节随机主密钥 |
| **SK** | Space Key，空间对称密钥（由档位决定如何封装/公开） |
| **KEK** | 由口令经 Argon2id 派生 |

---

## 3. 目录布局

```
<vault>/
  cairn.toml                       # 明文：版本、库 ID、KDF 参数、封装 MK、算法参数
  pool/                            # 内容真源（对象池）
    spaces/<space_id>              # 空间记录（CBOR，加密）：可见性、成员、封装后的 SK
    chunks/<cid[:2]>/<cid>         # 块密文，文件名 = CID
    objects/<oid[:2]>/<oid>        # 当前（head）信封：明文 space_id + 密封的 manifest
    manifests/<h[:2]>/<h>          # 历史 manifest 密文（不可变），h = BLAKE3(密文)
  db/
    structure.db                   # 结构真源（关系/成员/标签/属性），半加密，不可重建
  .cairn/                          # 仅派生，全可删可重建
    index.db                       # 内容对象索引（由 pool/ 派生）
    cache/  logs/
  .lock                            # 单写者锁
```

- 分片深度 1 级（`[:2]`，256 桶）起步，桶满可在后续版本升 2 级（需迁移）。
- 文件名只含 **CID / OID / 内容哈希 / ULID**，**不含任何明文**。
- `db/` 与 `.cairn/` 分开是**语义分区**（不是安全边界）：`.cairn/` 是"可删可重建"，`db/structure.db` 是权威——清理 / 重建**只允许碰 `.cairn/`**。

---

## 4. 身份与密钥层级

### 4.1 身份（Identity）

- 每库一个身份种子（32B 随机）→ 派生 **Ed25519（签名）** 与 **X25519（密钥协商）** 密钥对。
- 身份私钥种子由 MK 封装后落盘；公钥即库的网络标识（peer id 取其短哈希）。
- 用途：签名 manifest（作者证明）、接收定向/公共空间密钥（X25519 协商）。

### 4.2 空间密钥（SK）

每个 Space 一把对称密钥 SK（32B）。SK 的**封装方式由可见性档位决定**（详见 `access.md`）：

| 档位 | SK 的形态 |
|---|---|
| 私密 private | 随机 SK，用 MK 封装 |
| 公共 communal | 组密钥，wrap 到各成员 X25519 公钥 |
| 公开 public | 已发布密钥（非秘密）或明文 |
| 定向 direct | 每对象内容密钥 CK，wrap 到收件人 X25519（或 PSK） |

### 4.3 子密钥派生

```
SK ──BLAKE3 derive_key(context)──▶
    ├─ addr_key  "cairn/v1/space/<id>/chunk-address"
    ├─ data_key  "cairn/v1/space/<id>/chunk-data"
    └─ meta_key  "cairn/v1/space/<id>/manifest-data"
```

MK 的封装：

```
passphrase ──Argon2id(salt, 参数)──▶ KEK(32B)
WrappedMK = AEAD(KEK, nonce, MK)                 # 存 cairn.toml
```

- MK 永不落盘明文。**改口令**只重封装 MK。
- **去重范围 = 空间**：块用 SK 派生密钥加密、CID 用 `addr_key` 计算 → 同一块只在同一空间内去重；不同空间即使内容相同也各自独立（不产生跨空间确认攻击）。

---

## 5. 分块（FastCDC）

- 算法：**FastCDC**（内容定义），插入/删除只影响局部边界 → 增量友好。
- 参数：`min=16 KiB`，`avg=64 KiB`，`max=256 KiB`。
- 对象 ≤ `min` → 单块；大对象流式分块，不整份入内存。

---

## 6. 内容寻址（CID）

```
CID = BLAKE3_keyed(addr_key, chunk_plaintext)    # 32B → 小写十六进制
```

- keyed hash：空间内可去重，空间外无法确认。
- 同块只写一次：`put` 前查 `chunks/<cid>` 是否已存在。
- 读取解密后**重算 CID 比对**，兼作完整性/防篡改校验。

---

## 7. 加密与文件格式

AEAD：**ChaCha20-Poly1305**（12B 随机 nonce，16B tag）。
> 说明：`cryptography`（至 50.x）未提供 XChaCha20-Poly1305，故采用 ChaCha20-Poly1305。单密钥下 12B 随机 nonce 碰撞概率可忽略；将来若需 24B nonce 可经 libsodium（PyNaCl）切换，并在 `cairn.toml` 记录算法标识。

### 7.1 块文件

```
[ver:1B=0x01][nonce:12B][AEAD_ciphertext(含16B tag)]
```

- key = 空间 `data_key`；AAD = CBOR`{v:1, kind:"chunk"}`。
- 不绑 OID：块在空间内共享。

### 7.2 清单文件

```
[ver:1B=0x01][nonce:12B][AEAD_ciphertext(含16B tag)]   # 明文为 CBOR manifest
```

- key = 空间 `meta_key`；AAD = CBOR`{v:1, kind:"manifest", oid:"<OID>"}`。
- 签名在**明文 CBOR 内**（`sig` 字段），加密之前计算，加密之后一并保护。
- **对象信封（envelope）**：head 文件实为 `ver ∥ CBOR{v, space_id, manifest:<上述封帧>}`。`space_id` 以明文置于信封外层，用于读取时先选对空间密钥；manifest 本体仍按空间密钥密封。这是"用空间密钥加密"与"读前需知道属于哪个空间"之间的必要折中。

---

## 8. 清单（Manifest，CBOR）

加密前为确定性 CBOR（RFC 8949）：

```
{
  "v": 1,
  "oid": "<ULID>",
  "space_id": "<space>",
  "type": "note" | "asset" | "project" | "blob",
  "mime": "application/x-cairn-note" | "image/png" | ...,
  "size": <明文总字节数 int>,
  "created": <unix ms int>,
  "updated": <unix ms int>,
  "chunks": [ {"cid": "<hex>", "size": <明文块长 int>}, ... ],
  "meta": { "title": "...", "tags": ["..."], "props": { ... } },

  "seq": <单调递增 int>,
  "prev": "<上一版 manifest 密文的 BLAKE3 hex>" | null,
  "author": "<Ed25519 公钥 hex>",
  "sig": "<Ed25519 对(本节除 sig 外所有字段的确定性 CBOR)的签名 hex>"
}
```

- **版本链**：更新时先把旧 head manifest 密文归档到 `manifests/<h>`（`h=BLAKE3(密文)`），新 manifest 的 `prev=h`、`seq+1`，再原子覆盖 head。
- **信任根**：远端 manifest 必须验 `author` 签名与 `prev` 链，方可用于同步（见 `access.md`）。

---

## 9. 数据库

数据库分两类，物理上分文件：**派生索引 `index.db`（可重建）** 与 **权威结构库 `structure.db`（不可重建）**。
由多库管理器统一打开——未来 P2P 连接时可把"涌入的索引流量"与结构库隔离，互不锁。

### 9.1 派生索引（`.cairn/index.db`，可重建）

解锁后遍历 `pool/objects/**` → 验签/解密 manifest 构建。明文、仅本地。

```sql
spaces(space_id PK, name, visibility, key_epoch, created)
objects(oid PK, space_id, type, mime, size, created, updated,
        seq, author, title, manifest_mtime)
obj_tags(oid, tag, PRIMARY KEY(oid, tag))
obj_chunks(oid, idx, cid, size, PRIMARY KEY(oid, idx))
chunks(cid PK, size, refcount)          -- refcount 派生缓存，非权威
meta(key PK, value)                     -- index_format_version, built_at ...
search_fts(oid, body)                   -- FTS5，供可提取纯文本的对象
```

- 全量重建是恢复兜底；增量在**写入路径**即时维护。
- 索引与磁盘冲突时，以磁盘 manifest 为准。
- **所有表都可删可重建**；这里不放任何"唯一一份"的数据。

### 9.2 结构库（`db/structure.db`，权威，半加密）

关系 / 成员 / 标签 / 属性是**结构数据，不是对象**（见 [`data-model.md`](./data-model.md) §4.2、§6.4）。
它们以**一等行**落在这里，**删了即丢，不可由 `pool/` 重建**。

```sql
relations(src_oid, dst_oid, kind, author, at, value_enc, value_hash)  -- 一等边，带署名
members(project_oid, member_oid, kind)                                -- 项目成员
tags(oid, tag_enc, tag_hash)
props(oid, key_enc, key_hash, value_enc)
```

- **半加密**：OID / 边用**明文**（ULID 是随机串，不泄语义）；带语义的值（标签 / 标题 / `props` 文本）用空间 `meta_key` **AEAD 加密**。
- **等值查询**：加密列另存 `keyed_hash(meta_key, value)` 列，支持等值匹配、不露明文；**不做**范围 / 模糊查询（结构数据本以等值和连接为主）。
- **整库加密（SQLCipher）** 作为可替换的**薄层**另研，**不与半加密叠加**（二选一；加密收在一层后面，换实现不改业务）。
- 结构库不参与对象 GC。

---

## 10. 读写流程与原子性

### 写入（提交点 = head manifest 的 rename）

1. 流式分块；算 CID；缺失块：加密 → 临时文件 → `fsync` → 原子 rename。
2. 组装 manifest（算签名、链 prev）→ 加密 → 临时文件 → `fsync` → 原子 rename 覆盖 head。
3. 归档旧 manifest；更新索引。

- 崩溃安全：**head rename 是提交点**。已写块无 manifest → 孤儿块，GC 回收。

### 读取

1. 读 head manifest → 解密 → 验 AAD/OID/签名。
2. 按 `chunks` 顺序读块 → 解密 → 重算 CID 校验 → 拼接明文流。
3. 任一块缺失/校验失败 → 报告损坏对象，不静默降级。

---

## 11. 删除与垃圾回收

- **逻辑删除**：删除 head manifest（真源）；可选回收站区（后续）。
- **GC（mark-and-sweep，权威）**：扫所有现存 head + 历史 manifest（按保留策略）→ 活跃 CID 集 → 删除未引用块与空目录。
- `refcount` 仅加速，不作权威；GC 需解锁。

---

## 12. 并发与锁

- **单写者**：`<vault>/.lock`（OS 文件锁）。
- 多读者安全（只读已提交文件）；同进程写入串行化。
- 网络盘 / 云同步目录：未验证，不推荐。

---

## 13. 版本与迁移

- `cairn.toml`：`format_version`；块/清单头：`ver`；manifest：`"v"`。
- 迁移按版本分支升级，写新格式并原子替换，不就地破坏。

---

## 14. 威胁模型（摘要）

**防**：静态数据保密（按档位）、篡改检测（AEAD + CID 重算）、跨空间确认攻击（keyed CID + 空间隔离）、远端伪造（manifest 签名 + 版本链）。

**不防**：解锁态内存取证 / 键盘记录 / 已攻陷终端；流量元数据（详见 `access.md`）。

---

## 15. 公开内容 / P2P 前瞻

- 内容寻址利于复制：块与 manifest 可整体搬迁，无密钥即不可读。
- 空间 = 共享与去重的单位；公开空间可全局去重。
- 详细档位语义、密钥分发、发现与同步见 [`access.md`](./access.md)。

---

## 16. 依赖

| 用途 | 库 |
|---|---|
| 分块 | `fastcdc` |
| 哈希 / KDF 派生 | `blake3` |
| AEAD | `cryptography` |
| 签名 / 协商 | `cryptography`（Ed25519 / X25519） |
| Argon2id | `argon2-cffi` |
| CBOR | `cbor2` |
| 其余 | stdlib：`os` `pathlib` `secrets` `struct` `sqlite3` |

> 实现前核对各库 API，有出入以实际为准并回写本文档。

---

## 17. 待定问题

1. 分片深度与阈值。
2. 历史 manifest 的保留策略（全留 / N 版 / 时间窗）。
3. 系统钥匙串缓存 MK 的默认开关。
4. FTS 文本提取契约（依赖 L3）。
5. 结构库的整库加密（SQLCipher）取舍与许可核实。
6. 结构库 `keyed_hash` 列的具体设计（哪些列需要等值查询）。
7. 内容对象的远期物理打包（pack）——结构不再做对象后已不紧迫。

---

## 18. 常量表（草案）

| 常量 | 值 |
|---|---|
| 块 min / avg / max | 16 KiB / 64 KiB / 256 KiB |
| 哈希 | BLAKE3-256，keyed（CID），derive_key（子密钥） |
| AEAD | ChaCha20-Poly1305，12B nonce，16B tag |
| 签名 | Ed25519 |
| 协商 | X25519 |
| Argon2id | time=3，mem=64 MiB，par=4，salt=16B，输出 32B |
| 身份 | ULID（26 字符 Crockford Base32） |
| 清单编码 | CBOR（RFC 8949 确定性编码） |
| 分片 | `[:2]` |
| 文件头 | `ver(1B) ∥ nonce(12B) ∥ ciphertext+tag` |
