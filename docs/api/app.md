<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# app（应用组合根）

> **组合根 / 编排层**：组合内核 + 领域 + `ui_tools`，按平台发布。
> **只有它认识领域** —— 建域服务（`Feature`）并注入 UI，UI 自己不 new 领域对象。

## 包入口

平台分派（`python -m app`）。非 Windows 平台**没有 UI**，打印提示并返回退出码 2。

::: app

## 领域装配

静态声明的领域容器：已经有了就取用，没有才建（内核是单例，域服务只需建一次）。

::: app.win

## Windows 根壳

`CairnApp.open()`（开库 + 组装）与 `.run()`（套主题、建窗、进事件循环）——
只暴露这两件事，Qt 启动样板不外泄。

::: app.win.windows

!!! warning "实验性"

    界面正在重建（见「[现状](../index.md#_2)」）。这里的组合与布局会频繁变动，
    **不要**在它之上写扩展；领域 Facet 的稳定形态待 UI 内核落地后才有定论。

!!! note "Linux"

    `app.linux` 目前是**占位包**（本平台不要 UI）；macOS 暂缓，Android 未来另择 UI 框架。
