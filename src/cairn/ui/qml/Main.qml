// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 真实窗口入口：无边框自绘标题栏。
// 内容放在 Loader 里，方便开发时热重载（只重载 Shell，不重建窗口）。
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
    color: CairnTheme.bg
    title: "Cairn"
    flags: Qt.Window | Qt.FramelessWindowHint

    // 按屏幕可用区域挑一个合适比例并居中，避免一开就过大/偏心。
    Component.onCompleted: {
        const aspect = 3 / 2;
        const availW = Screen.desktopAvailableWidth > 0 ? Screen.desktopAvailableWidth : Screen.width;
        const availH = Screen.desktopAvailableHeight > 0 ? Screen.desktopAvailableHeight : Screen.height;
        let w = Math.min(availW * 0.8, 1440);
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

    Loader {
        id: rootLoader
        objectName: "rootLoader"
        anchors.fill: parent
        // 热重载：由 app.py 注入的 reloader.shellSource 驱动（带版本号 URL）。
        // 未注入时（如单独预览 Main.qml）回退到相对路径。
        source: typeof reloader !== "undefined" && reloader ? reloader.shellSource : "Shell.qml"
    }

    // 无边框窗没有原生可拖边，自己补命中区，交给系统缩放（跟手）。
    component ResizeArea: MouseArea {
        required property int edges
        property int band: 5
        cursorShape: {
            if (edges === (Qt.LeftEdge | Qt.TopEdge) || edges === (Qt.RightEdge | Qt.BottomEdge))
                return Qt.SizeFDiagCursor;
            if (edges === (Qt.RightEdge | Qt.TopEdge) || edges === (Qt.LeftEdge | Qt.BottomEdge))
                return Qt.SizeBDiagCursor;
            if (edges === Qt.LeftEdge || edges === Qt.RightEdge)
                return Qt.SizeHorCursor;
            return Qt.SizeVerCursor;
        }
        enabled: win.visibility !== Window.Maximized
        onPressed: win.startSystemResize(edges)
    }

    ResizeArea {
        edges: Qt.LeftEdge
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: band
    }
    ResizeArea {
        edges: Qt.RightEdge
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: band
    }
    ResizeArea {
        edges: Qt.TopEdge
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: band
    }
    ResizeArea {
        edges: Qt.BottomEdge
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        height: band
    }
    ResizeArea {
        edges: Qt.LeftEdge | Qt.TopEdge
        anchors.left: parent.left
        anchors.top: parent.top
        width: band
        height: band
    }
    ResizeArea {
        edges: Qt.RightEdge | Qt.TopEdge
        anchors.right: parent.right
        anchors.top: parent.top
        width: band
        height: band
    }
    ResizeArea {
        edges: Qt.LeftEdge | Qt.BottomEdge
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        width: band
        height: band
    }
    ResizeArea {
        edges: Qt.RightEdge | Qt.BottomEdge
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        width: band
        height: band
    }
}
