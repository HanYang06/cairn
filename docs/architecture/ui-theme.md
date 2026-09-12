<!-- SPDX-FileCopyrightText: 2026 HanYang06 -->
<!-- SPDX-License-Identifier: Apache-2.0 -->

# UI 主题与美化（Qt / PySide6）

> 定位：**桌面 APP，不是 Web**。要好看，但不为炫技。可维护、可控、许可证干净优先。
> 相关：[`note-model.md`](./note-model.md) §9（捕捉面 / 编辑面分离）。

状态：**草案 v0.1**

---

## 1. 目标与约束

- **好看**：深色优先、留白、克制动效，呼应品牌（冷灰石 + 暖赭 + 苔绿）。
- **可控**：优先原生 Qt；不引入会污染许可证的重框架。
- **快**：捕捉面（热键）必须秒开，不能背 Web 启动的锅。
- **可维护**：主题以"令牌 + QSS"集中管理，不散落在各控件里。

---

## 2. 原生 Qt 的美化手段（能力清单）

| 手段 | 能做什么 | 代价 |
|---|---|---|
| **QSS（Qt Style Sheets）** | 类 CSS 主题：颜色、边框、圆角、padding、状态选择器 | 不是完整 CSS：**无 box-shadow**、选择器有限 |
| **QPalette** | 基色（配合 QSS） | 单独用较原始 |
| **Fusion 风格** | 跨平台统一底座，对 QSS 友好 | —— |
| **自绘 / Delegate** | 卡片、列表项、连接线、图 | 要写 `QPainter`/`QStyledItemDelegate` |
| **动画框架** | `QPropertyAnimation` / `QParallelAnimationGroup` / easing | 够用，不如 CSS 顺滑 |
| **图形效果** | `QGraphicsDropShadowEffect` / `BlurEffect` / `OpacityEffect` | **列表里慎用，性能/兼容有坑** |
| **图标** | SVG（`QtSvg`，可染色）/ 图标字体 | 需准备资源 |
| **字体** | 内置一款无衬线（如 Inter）保证一致 | 打包体积 |
| **无边框窗** | 自绘标题栏、圆角、现代感 | 跨平台有坑（缩放/拖拽） |

**结论**：用 **Fusion + 集中式 QSS + 少量自绘** 就能做出很体面的暗色应用；动效只做**功能性**的（淡入、滑动），不做装饰性花活。

---

## 3. Web 混合（QtWebEngine）

富编辑 / 画布这类"重表现"的界面，原生 Qt 自绘成本极高，交给 Web：

- 块编辑：ProseMirror / Tiptap
- 画布/手绘：Excalidraw + perfect-freehand

**注意**：QtWebEngine 重、冷启动慢——**只用于编辑面，不用于捕捉面**（见 `note-model.md` §9）。可预加载以缓解。

---

## 4. 第三方主题库（许可证是重点）

| 库 | 风格 | 许可证 | 结论 |
|---|---|---|---|
| QDarkStyleSheet | 暗色 QSS | **MIT**（代码）+ CC-BY-4.0（图） | ✅ 可用 |
| qt-material | Material QSS | **BSD-2-Clause** | ✅ 可用 |
| PySide6-Fluent-Widgets（zhiyiYo） | Fluent，很漂亮 | **疑 GPLv3（需核实）** | ⚠️ 发布前必查，GPL 会传染 |
| qtdarktheme | 主题助手 | 需核实 | ⚠️ 查后再用 |

**红线**：本项目 Apache-2.0。**任何 GPL/AGPL 依赖都会传染**，宁可不美也别踩。

---

## 5. 我们的品牌主题（结合 logo）

### 5.1 色板（令牌）

```
深色（默认）
  bg         #1C1A18
  surface    #242120
  elevated   #2E2A26
  border     #3A3F44
  text       #E8E4DC
  muted      #9A938A
  accent     #C77B3C   （赭）
  accent-2   #5B6E4F   （苔绿）

浅色
  bg         #F2ECE3
  surface    #FFFFFF
  border     #D8D0C4
  text       #2E2A26
  muted      #7A736A
```

- **一套令牌，两套值**（深/浅），QSS 由令牌拼出，切换即换值。
- 强调色**克制**：只用于选中、链接、主按钮。

### 5.2 其余规范

- **字体**：内置一款无衬线（Inter / HarmonyOS Sans），行高宽松。
- **圆角**：统一 6–8px；卡片 10–12px。
- **间距**：4 的倍数；留白宁可多。
- **图标**：单色线性 SVG，随文字色染色。
- **动效**：只做 120–200ms 的功能动效（淡入/位移），提供"减少动效"开关。

---

## 6. 落地路线

| 阶段 | 内容 |
|---|---|
| **P0** | Fusion + 令牌化 QSS（深/浅切换）+ 应用字体/图标 |
| **P1** | 自绘列表/卡片/反链面板；功能性微动效 |
| **P2** | Web 富编辑 / 画布（QtWebEngine，编辑面专用） |

---

## 7. 待核实 / 待定

1. PySide6-Fluent-Widgets 等库的准确许可证（红线）。
2. 是否需要无边框窗（现代感 vs 跨平台坑）。
3. 内置字体选型与体积。
4. 减少动效 / 高对比等无障碍开关是否纳入 v1。
