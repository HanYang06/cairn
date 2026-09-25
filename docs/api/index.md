<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# API 参考

!!! info "这一节是自动生成的"

    下面所有签名、类型、docstring 都由 [mkdocstrings](https://mkdocstrings.github.io/)
    直接从 `src/**` 抽取（走 AST，不执行副作用代码）。**没有第二份会过期的拷贝** ——
    改代码 / 改 docstring，这里就跟着变。请**不要**手写 API 说明。

## 稳定度分级

本项目的 API 面**不承诺稳定**（0.0.1、pre-alpha）。按"能不能碰"分三档：

| 档 | 范围 | 说明 |
|---|---|---|
| **公共面**（较稳） | `core` 的 `Core` / `Signal` / `Storage` / `ConfEngine` / `core.types`；`feature` 的域与数据类；`ui_tools.core` 的接入点 | 会随设计走，但**改了会在这里体现**，且尽量留过渡 |
| **界面工具箱**（在长） | `ui_tools.component` / `ui_tools.layout` / `ui_tools.page` | UI 内核正在重建，增长最快的一层 |
| **内部**（别依赖） | `_` 开头的名字、`app.win.*` 的私有组合、`core.storage` 的实现细节 | 随时会动；`ui_tools` 连 `core.storage` 都不许 import |

## 四层

```text
core(L0)  ←  feature(L3)  ←  app(组合根)
                     ↑
                ui_tools(工具箱)
```

| 页 | 覆盖 |
|---|---|
| [core（底座）](core.md) | 内核本体、信号引擎、存储、配置引擎、类型地基 |
| [feature（领域）](feature.md) | note / project 域，asset / canvas / group / relation / signature 共享件 |
| [ui_tools（界面工具层）](ui-tools.md) | 声明树、编译管线、绑定、模型、主题、组件与布局 |
| [app（应用组合根）](app.md) | 领域装配与平台入口（Windows 根壳） |

## 怎么读

- **先看「[架构](../architecture/index.md)」再看这里**：这里回答"签名是什么"，
  架构文档回答"为什么长这样"。反过来读会一头雾水。
- 每页顶部的包 docstring 通常写着该层的**边界与红线**，比正文更值得读。
- 想找某个词 → 「[术语表](../reference/glossary.md)」。
