# 生态调研：哪些用轮子，哪些自造

> 目标：不闭门造车。逐项列出"需求 → 现成轮子 → 语言 → 许可 → 采用建议"。
> 原则：**能借的借，借不到的自己造；核心差异化必须自造。**

状态：**草案 v0.1**。标注「需核实」的条目，落地前必须再查一次许可证/成熟度。

---

## 0. 结论速览

| 需求 | 轮子 | 语言 | 许可 | 采用 |
|---|---|---|---|---|
| P2P 网络 | **py-libp2p** | Python | MIT/Apache | ✅ 首选 |
| AI 接入 | **MCP Python SDK** | Python | MIT | ✅ 首选 |
| 富文本/块编辑 | **ProseMirror / Tiptap** | JS/TS | MIT | ✅ Web 面 |
| 手绘画布 | **Excalidraw** | TS | MIT | ✅ Web 面 |
| 笔迹平滑 | **perfect-freehand** | JS | MIT | ✅ |
| 形状识别 | **$P 模板识别**（自实现）/ 端侧小模型 | Py/JS | 自造 | ✅ 先模板后模型 |
| 全文检索 | **SQLite FTS5** | C/Py | 公有领域 | ✅ 已用 |
| 协作 CRDT | **Yjs** | JS | MIT | ⏸ 后置 |
| 画布 SDK（备选） | tldraw | TS | **需核实（疑商用授权）** | ⚠️ 谨慎 |
| 矢量几何 | shapely | Py | BSD | ✅ 备用 |
| 加密/哈希/分块 | cryptography/blake3/fastcdc | Py | 见依赖 | ✅ 已用 |

**自造（差异化，不可替代）**：加密对象池（已完成）、基板格式、关系/族谱、索引、Qt 外壳、AI 工具暴露方式。

---

## 1. 编辑 / 基板

| 项目 | 语言 | 许可 | 说明 |
|---|---|---|---|
| ProseMirror | JS/TS | MIT | 无头富文本与文档模型，生态最成熟 |
| Tiptap | JS/TS | MIT（部分 pro 扩展付费） | ProseMirror 的 DX 封装，上手快 |
| Lexical | JS/TS | MIT | Meta 出品，现代编辑器框架 |
| Slate | JS/TS | MIT | 可定制，生态略小众 |
| Excalidraw | TS | MIT | 手绘风白板/画布，可做画布底座 |
| tldraw | TS | **需核实（tldraw license，免费版疑带水印）** | 画布 SDK，强但许可受限 |
| perfect-freehand | JS | MIT | 点序列 → 好看的笔画形状 |
| rough.js | JS | MIT | 手绘风格图形 |
| Qt 原生 | Py/C++ | LGPL/商业 | `QTextEdit`/`QGraphicsView`；富编辑能力有限 |

**建议**：数据格式用我们自己的 **substrate 片段（CBOR）**，编辑器的文档 JSON 只作**投影/输入**。
- 富文本/块：`ProseMirror`（或 Tiptap）
- 画布/手绘：`Excalidraw`（MIT，避开 tldraw 的许可风险）+ `perfect-freehand`
- Qt 侧用 `QtWebEngine` 承载 Web 编辑器；**捕捉面保持原生**（及时性）。

---

## 2. 手绘 → 标准形状（形状识别）

| 方案 | 说明 | 建议 |
|---|---|---|
| `$1 / $N / $P` 识别器 | 模板匹配，学术经典，易移植 | ✅ **先上**，够覆盖线/三角/圈/箭头 |
| 端侧小模型（ONNX Runtime） | 更高精度，可离线 | ✅ 后上，精度不足时 |
| Google QuickDraw / sketch-rnn | 数据/模型重 | ❌ 过重 |
| shapely / numpy | 几何拟合、简化、规整 | ✅ 辅助 |

**建议**：先实现 `$P` 模板识别（纯 Python/JS 皆可），把"歪扭 → 标准图元"跑通；精度不够再引端侧小模型。**只存识别后的形状**（见 `note-model.md` §6）。

---

## 3. 协作 / CRDT（后置）

| 项目 | 语言 | 许可 | 说明 |
|---|---|---|---|
| Yjs | JS | MIT | 最成熟，配 `y-prosemirror`/`y-excalidraw` |
| Automerge | Rust + JS | MIT | 历史/时间旅行强；**Python 绑定成熟度需核实** |
| diamond-types | Rust | MIT | 高性能 CRDT |

**建议**：实时协作本阶段**不做**（`note-model.md` 已后置）。将来若做，Web 编辑器侧选 `Yjs` 最省力。

---

## 4. 本地优先同步 / P2P

| 项目 | 语言 | 许可 | 状态 |
|---|---|---|---|
| **py-libp2p** | Python | MIT/Apache | 已过实验期；QUIC/TCP/WebSocket、Noise/TLS、mDNS、Kad-DHT、GossipSub、中继、打洞齐全 |
| go/rust-libp2p | Go/Rust | MIT/Apache | 更成熟更快，但要引入非 Python 进程 |
| Hypercore / Dat / Willow | JS/Rust | MIT（多数） | 另一类本地优先复制，绑定参差 |
| IPFS | Go/Rust | MIT | 理念相近，偏重 |

**建议**：**py-libp2p 作为 P2P 底座首选**。我们的存储层已是内容寻址，P2P 层只需"want-list = 一组 CID" + libp2p 传输，天然对接。性能不够时再考虑 Rust 实现。

---

## 5. AI 接入

| 项目 | 语言 | 许可 | 说明 |
|---|---|---|---|
| **MCP Python SDK**（`mcp`） | Python | MIT | 把能力暴露成 tools，生态广（各类 MCP 客户端） |
| 自定义 skill 协议 | — | — | 无生态，需自造 |

**建议**：用 **MCP Python SDK** 把内核能力（读/写/订阅/建关系）暴露为 tools。这正好印证 `note-model.md` 的立场：**AI 不是作者，是工具调用者**；低能力 AI（规则）与高能力 AI（大模型）都走同一工具集。

---

## 6. 检索 / 索引

| 项目 | 语言 | 许可 | 说明 |
|---|---|---|---|
| SQLite FTS5 | C | 公有领域 | 已随 SQLite 用上，够用 |
| tantivy（tantivy-py） | Rust | MIT | 更强全文，需要时再换 |
| jieba / 分词 | Python | MIT | 中文分词（FTS5 中文需处理） |

**建议**：FTS5 起步；中文检索用分词预处理或 trigram。不够再上 tantivy。

---

## 7. 先前作品（读，不 fork）

| 项目 | 与我们关系 | 可借鉴 |
|---|---|---|
| Anytype / any-sync | 最近：本地优先+加密+P2P+对象图（许可**需核实**） | 数据模型、同步思路 |
| AppFlowy | Flutter+Rust，Notion 类 | 编辑器 UX、块模型 |
| SiYuan | 本地优先、块、SQLite | 索引/块结构 |
| Logseq | outliner、文件本体 | 双链、daily note UX |
| Obsidian | 闭源，插件生态 | UX 范式 |

**结论**：**读它们的数据模型与 UX，不 fork**（地基不同：明文文件 vs 加密对象池，见 `note-model.md`）。

---

## 8. 分工总账

- **自造**：加密对象池 ✅、substrate 格式、关系/族谱、索引/反链、Qt 外壳、AI 工具暴露。
- **借轮子**：py-libp2p（P2P）、MCP（AI）、ProseMirror/Excalidraw/perfect-freehand（Web 编辑/画布）、SQLite FTS5、shapely、Yjs（后置）。

---

## 9. 待核实清单

1. tldraw 许可（免费版是否带水印、商用条件）。
2. Anytype / any-sync 许可是否 OSI。
3. Automerge 的 Python 绑定成熟度。
4. Excalidraw 作为可嵌入 SDK 的成熟度与体积。
5. MCP Python SDK 的当前 API 形态（tools/resources/prompts）。
