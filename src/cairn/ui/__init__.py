# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""界面层（PySide6 / Qt Quick + QML）。

组织纪律：
  qml/         主界面（Qt Quick），只做表现；主题走 theme 单例
  theme/       主题令牌 + 内置主题 + QSS 渲染（无 Qt 依赖，Widgets 备用）
  components/  可复用组件（叶子优先，只吃令牌）
  views/       页面（由 components 组装，不写样式）
  adapter      内核事件 → Qt 信号（主线程）
  app          应用入口与主窗口
"""
