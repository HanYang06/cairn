<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# 进度 / TODO

> 状态：进行中 / 已定 / 已废弃。完成后移入 `changes.md`，或直接删除。
> 细则以 `docs/architecture/*.md` 与代码为准，本文件只记「还没做 + 在做」。

## 底层（数据内核 + 通信主干 + UI 内核 + App）

### 数据内核 `core`
- [x] 存储底座 `Bucket` / `Block` / `catalog` / `version` / `table`；DB 重构切片 1–3
  （表列改名、`type` 整数码、`block.data` 收口、载体随机命名、去 `version_heads`、`relation.domain`、类型索引）。
- [x] 通信主干 `core/signal`（`events` / `bus` / `service`）；统一、静态挂载。
- [x] 类型 / 编解码 / `Vault`。
- [ ] `core/conf`：现仅 `core.py` 有常量，`feature` / `signal` / `storage` / `confsys` 待填。
- [ ] 数据库迁移机制（`catalog_version` → 旧库检测 / 迁移）。
- [ ] pack 压实 / gc。

### 领域 `feature`
- [x] note 拆「数据 `NoteData(Block)` + 域服务 `Note(Domain)`」；行编辑 / 版本 / 关系。
- [ ] 其余领域按同口径拆（asset / canvas / group / project / relation / signature / provenance）。
- [ ] 图片 / 音频转码（不传染库）；大正文透明分片（`Bucket.put_content`）。
- [ ] **跨域编排**（域间关系 / 订阅）——交由 App 承担，尚未落地。
- [ ] **变更签名**（非原作者 / `prev` 链；`alg` 日后换 `ed25519`）预留未实现。
- [ ] `note/shapes.py` 形状集 v2（含图形超出 / 图形未定义）未落。

### UI 内核 `ui_tools`（工具箱）
- [x] 声明树 `Node` / 注册表 / 元数据 / 路径；`compile` 管线 + Widgets 翻译器；atoms / list。
- [x] 配置 `Conf` / `Schema` / `apply_config`；绑定 `Bind` / `compile` + Qt 连接；`Session` / `Model` / `Bridge` /
  `QtListModel`；`Theme`。
- [x] `WindowHost` 根壳 + 路由；架构红线测试。
- [ ] 多页 Tab 宿主；配置 item 词表校验；主题文件系统（`config/theme/*.json`）；QML 岛承载器。

### App `src/app`
- [x] `Feature` / `build` / `NoteFacet`；`win` 入口；`__main__` 平台分发。
- [ ] `win/backend`（会话 / 桥）、`win/windows`（真外壳部件：标题栏 / 导航 / 编辑器 / 检查器）。
- [ ] 桌面打包：`packaging/cairn.spec` + 构建脚本。

## 编辑器 / 工具线（待 UI 外壳恢复后）
- [ ] 跨行选区 + 拖拽出视窗自动滚动。
- [ ] 撤销 / 重做栈。
- [ ] 添加型底层（表格 / 画板 / 多媒体）；查询型（查找替换）。
- [ ] 工具重排与持久化；笔记列表形态；画板绘制；多媒体拖入。

## 远期
- [ ] **Project（重）**：建在 block / body / bucket 之上；项目管理 + 类 GitHub 社区化；todo 验证器。
- [ ] 任务与进度、应用上下文。
- [ ] P2P / 服务端（顶层包待重设）、成员 / 社区、传输加密。

## 工程债
- [x] 架构文档回写：`storage.md`（表/列/随机 pack/无 heads）、`domains.md`（数据+域服务、路径）、
  `kernel.md`（§1.6 通信主干）、`data-model.md`（映射表 + 导引）、`ui-kernel.md` / `ui-theme.md` /
  `note-model.md` / `access.md` / `network.md` / `ecosystem.md`（现状导引、删旧 QML/Backend/net/server）。
  **全部与代码对齐**。
- [ ] 可复现构建、代码签名（Authenticode）；包体瘦身。
- [ ] Linux 服务端 / CLI / Docker（待服务端）。
