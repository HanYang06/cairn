"""界面层（PySide6 / Qt Widgets）。

组织纪律（比前端严格）：
  theme/       主题令牌 + 内置主题 + QSS 渲染（无 Qt 依赖）
  components/  可复用组件（叶子优先，只吃令牌）
  views/       页面（由 components 组装，不写样式）
  adapter      内核事件 → Qt 信号（主线程）
  app          应用入口与主窗口
"""
