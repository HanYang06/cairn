// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 真实窗口入口：无边框自绘标题栏 + Shell 内容。
import QtQuick
import QtQuick.Window
import "theme"

Window {
    id: win
    width: 1280
    height: 800
    minimumWidth: 960
    minimumHeight: 600
    visible: true

    // 按屏幕可用区域挑一个合适比例并居中，避免一开就过大/偏心。
    Component.onCompleted: {
        const aspect = 16 / 10;
        const availW = Screen.desktopAvailableWidth > 0 ? Screen.desktopAvailableWidth : Screen.width;
        const availH = Screen.desktopAvailableHeight > 0 ? Screen.desktopAvailableHeight : Screen.height;
        let w = Math.min(availW * 0.86, 1600);
        let h = w / aspect;
        if (h > availH * 0.88) {
            h = availH * 0.88;
            w = h * aspect;
        }
        width = Math.round(Math.max(w, 960));
        height = Math.round(Math.max(h, 600));
        x = Math.round((availW - width) / 2);
        y = Math.round((availH - height) / 2);
    }
    color: CairnTheme.bg
    title: "Cairn"
    flags: Qt.Window | Qt.FramelessWindowHint

    Shell {
        anchors.fill: parent
    }
}
