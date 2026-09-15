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

## 工程 / 产品

- 2026-09-14 · 已定 · skill 放 `.agents/skills/`；根 `AGENTS.md` 只做索引；`rules`=约束、`memory`=现状。
- 2026-09-14 · 已定 · 布局契约：三栏 SplitView，属性栏默认收起；列表交互照 VS Code、不做过渡动画。
- 2026-09-14 · 已定 · 删除先入回收站；**版本只记内容变化**（元数据不产生历史）。
- 2026-09-14 · 已定 · 分发：源码与 Windows 桌面 P0（PyInstaller onedir + Inno）；macOS 暂缓。
- 2026-09-16 · 已定 · UI：精简、自然；色盘照 GitHub，圆角与阴影照苹果；中英统一等宽字体
  （链条首为「更纱黑体 / Sarasa Mono SC」）。
- 2026-09-16 · 已定 · 只引不传染许可（MIT/BSD/Apache）的依赖；GPL/AGPL 禁用。
