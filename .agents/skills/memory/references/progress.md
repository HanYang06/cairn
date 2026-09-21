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
- [x] **降级**：`Asset` / `Canvas` / `Group` 去 `Domain`，回归纯 `Block` 数据结构（构造入口在数据类）。
- [x] **最小类型表** `core/types/kind.py`：`TypeInfo{type, role, name, fields, deps, units}`，定义时登记。
- [x] **文件归位（第一批）**：`feature/shared/`（数据结构 / 值 / 设施）；`note/edit/` 三分（body/text/style）。
- [x] **`note/types.py` 拆包**：`body.py` / `data.py` / `service.py`（纯搬运）。
- [x] **操作归位**：编辑操作从 `NoteData` 迁到 `Note`（数据只留载体 + 读视图）。
- [x] **类型枚举**：`feature/shared/kinds.py` 的 `Kind(StrEnum)`；类型表 `str()` 归一。
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
- [x] `Feature`（领域容器）；`win` 组合根 `CairnApp.open()/run()`；`__main__` 平台分发。
- [x] **根结构 = 大方框 + 格子 + 槽**：`CairnApp` 自己搭结构（顶带 / 主体 / 底栏 + `nav`/`main` 槽）；
  `NoteFacet` 提供 `nav`/`page` 部件、内容工具条 + 卡片舞台；真实笔记投影（`win/backend`）；
  卡片 / 详细两密度；主题从 `config/theme` 加载。
- [ ] **对象驱动生成**：领域对象 → `Facet` 自动出 `parts()`（nav / page / 卡片…；当前手写）。
- [ ] 顶带抽屉（搜索 / 命令之外的功能）；任务栏真实任务；边板（检查器 / 关系 / 版本）。
- [ ] 笔记编辑页（专注态）；镜头筛选（笔记 / 项目混排 + 颜色区分）。
- [ ] 毛玻璃真 Acrylic（DWM）与字体策略。
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
