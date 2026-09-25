<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# feature（领域）

> L3：**域**（Note / Project）+ **共享件**（`shared/`）。
> 只依赖 `core` 的公共 API；**域之间互不依赖**，跨域协作归 App。

## 包入口

域与共享件从 `feature` 一处可导入：

::: feature
    options:
      members: false

## 笔记域

数据（`NoteData`）+ 域服务（`Note`）：创建 / 读写 / 落盘 / 编辑操作。
正文模型（行序列 + 行内区间样式）见 [`note-model.md`](../architecture/note-model.md)。

::: feature.note

## 项目域

成员的具名容器（走 `contains` 关系）。

::: feature.project

## 共享件

非域的跨域内容：asset / canvas / group / signature / relation / provenance / base / kinds。
**它们都是 `Block` 子类或工具单元，不是域。**

::: feature.shared
