// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

pragma Singleton

import QtQuick

// 主题令牌：精简、自然；色盘参照 GitHub，圆角与阴影参照苹果。
// 组件不得硬编码颜色/圆角/间距，一律引用这里。
QtObject {
    // 深浅可切换：默认亮色
    property bool dark: false
    // 无障碍开关
    property bool reduceMotion: false
    property bool highContrast: false

    // ===== palette（GitHub Primer）=====
    readonly property color bg: dark ? "#0D1117" : "#FFFFFF"
    readonly property color chrome: dark ? "#010409" : "#F6F8FA"
    readonly property color surface: dark ? "#0D1117" : "#FFFFFF"
    readonly property color elevated: dark ? "#161B22" : "#FFFFFF"
    readonly property color border: highContrast ? (dark ? "#6E7681" : "#8C959F") : (dark ? "#30363D" : "#D0D7DE")
    readonly property color borderStrong: highContrast ? (dark ? "#8B949E" : "#6E7781") : (dark ? "#484F58" : "#AFB8C1")
    // 结构分隔用的更淡边界（软化页面观感，不喧宾夺主）
    readonly property color borderFaint: highContrast ? (dark ? "#484F58" : "#AFB8C1") : (dark ? "#21262D" : "#E6EAEF")
    readonly property color text: highContrast ? (dark ? "#FFFFFF" : "#090C10") : (dark ? "#E6EDF3" : "#1F2328")
    readonly property color muted: highContrast ? (dark ? "#D0D7DE" : "#424A53") : (dark ? "#8B949E" : "#656D76")
    readonly property color faint: highContrast ? (dark ? "#AFB8C1" : "#57606A") : (dark ? "#6E7681" : "#6E7781")
    readonly property color accent: dark ? "#2F81F7" : "#0969DA"
    readonly property color accentAlt: dark ? "#3FB950" : "#1A7F37"
    readonly property color accentText: "#FFFFFF"
    readonly property color selection: dark ? "#1F6FEB44" : "#DDF4FF"
    readonly property color hover: dark ? "#161B22" : "#F3F4F6"
    readonly property color danger: dark ? "#F85149" : "#CF222E"

    // ===== shadow（苹果式：低透明、大模糊、小偏移）=====
    readonly property color shadowColor: dark ? "#66000000" : "#14000000"
    readonly property int shadowBlur: 24
    readonly property int shadowOffset: 4

    // ===== radius（收敛、自然）=====
    readonly property int radiusSm: 6
    readonly property int radius: 8
    readonly property int radiusLg: 10
    readonly property int radiusXl: 12

    // ===== spacing =====
    readonly property int spaceXs: 4
    readonly property int spaceSm: 8
    readonly property int spaceMd: 12
    readonly property int spaceLg: 16
    readonly property int spaceXl: 24

    // ===== typography（中英统一等宽）=====
    readonly property var fontFamilies: ["Sarasa Mono SC", "Cascadia Mono", "Consolas", "Noto Sans Mono CJK SC", "monospace"]
    readonly property string fontFamily: "Sarasa Mono SC"
    readonly property string iconFont: "Segoe MDL2 Assets"
    readonly property string monoFont: "Sarasa Mono SC"
    readonly property int fsTiny: 11
    readonly property int fsSmall: 12
    readonly property int fsBody: 13
    readonly property int fsLarge: 15
    readonly property int fsTitle: 22

    // ===== layout metrics =====
    readonly property int titleBarH: 38
    readonly property int activityW: 48
    readonly property int sideBarW: 264
    readonly property int tabBarH: 36
    readonly property int statusH: 24

    // ===== motion =====
    readonly property int durFast: reduceMotion ? 0 : 120
    readonly property int durBase: reduceMotion ? 0 : 180
    readonly property int durSlow: reduceMotion ? 0 : 260
}
