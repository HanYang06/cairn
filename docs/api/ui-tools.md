<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# ui_tools（界面工具层）

> 界面**工具箱**：声明树 / 编译 / 绑定 / 模型 / 主题 / 组件 / 布局。
> **不认识领域** —— 不 import `feature`、不碰 `core.storage`（有架构测试断言）。

## 包入口

工具箱的公共面收在 `ui_tools.core`：

::: ui_tools
    options:
      members: false

## UI 内核（Qt-free）

接入点、声明树基元、词汇表与编译管线。**这一层不依赖 Qt**；
Qt 只在 `ui_tools.core.qt` 出现（边界）。

::: ui_tools.core

## 组件

原子（`Label` / `Button` / `Field` / …）与结构件（`Toolbar` / `ListPanel` / …）。

::: ui_tools.component

## 布局

**纯几何组织器**（`VBox` / `HBox` / `Grid` / `Split` / `Stack`），不进主题词汇表。

::: ui_tools.layout

## 页面

页面层独立扩展点。

::: ui_tools.page
