// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

pragma Singleton

import QtQuick

QtObject {
    // 深浅可切换：默认亮色
    property bool dark: false
    // 无障碍开关
    property bool reduceMotion: false
    property bool highContrast: false

    // ===== palette =====
    readonly property color bg: dark ? "#1C1A18" : "#F4EFE7"
    readonly property color chrome: dark ? "#171512" : "#EDE6DB"
    readonly property color surface: dark ? "#242120" : "#FFFFFF"
    readonly property color elevated: dark ? "#2E2A26" : "#FFFFFF"
    readonly property color border: highContrast ? (dark ? "#6A7078" : "#B9AD9C") : (dark ? "#3A3F44" : "#E4DCCF")
    readonly property color borderStrong: highContrast ? (dark ? "#8A929C" : "#8A7F70") : (dark ? "#4A5058" : "#CFC4B3")
    // 结构分隔用的更淡边界（软化页面观感，不喧宾夺主）
    readonly property color borderFaint: highContrast ? (dark ? "#4A5058" : "#CFC4B3") : (dark ? "#2B2926" : "#EFE8DD")
    readonly property color text: highContrast ? (dark ? "#FFFFFF" : "#141210") : (dark ? "#E8E4DC" : "#2E2A26")
    readonly property color muted: highContrast ? (dark ? "#CFC8BE" : "#4A453E") : (dark ? "#9A938A" : "#7C746A")
    readonly property color faint: highContrast ? (dark ? "#A8A096" : "#6A635A") : (dark ? "#6E6860" : "#A89F93")
    readonly property color accent: "#D08A45"
    readonly property color accentAlt: dark ? "#7B9166" : "#6B7F5A"
    readonly property color accentText: dark ? "#1C1A18" : "#FFFFFF"
    readonly property color selection: dark ? "#3A332B" : "#F3E6D3"
    readonly property color hover: dark ? "#2A2724" : "#F0E9DE"
    readonly property color danger: "#C05A44"

    // ===== radius（更圆润）=====
    readonly property int radiusSm: 8
    readonly property int radius: 12
    readonly property int radiusLg: 14
    readonly property int radiusXl: 16

    // ===== spacing =====
    readonly property int spaceXs: 4
    readonly property int spaceSm: 8
    readonly property int spaceMd: 12
    readonly property int spaceLg: 16
    readonly property int spaceXl: 24

    // ===== typography =====
    readonly property string fontFamily: "Segoe UI"
    readonly property string iconFont: "Segoe MDL2 Assets"
    readonly property string monoFont: "Cascadia Code"
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
