# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""界面层（PySide6 / QtWidgets 宿主 + QML 岛）。

分层（由下到上）：
  component.py   `Component` 基类（中性：组件 / 布局 / 页面共用）
  components/    组件库：原子 + 结构件 + 编辑器（有行为；入主题词汇表）
  layout/        布局组织器：纯几何原语 VBox/HBox/Grid/Split/Stack（无行为）
  pages/         页面层：由结构件组装（Page 基类在此）
  theme/         主题配置引擎：令牌 + 选择器→声明块 + schema 生成（Qt-free 主体）
  signal/session/bridge/models/rows/format/motion  状态直通、模型、格式化、动画
  qmlhost.py     QML 岛承载器（QQuickWidget 封装）
  root.py        `App` 组合根
  window.py      `MainWindow` / `Shell`
  app.py         进程入口（`cairn` QML / `cairn --widgets` Widgets）
"""
