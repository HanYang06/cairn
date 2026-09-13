// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 右键上下文菜单：自绘（不用 QtQuick.Controls），与本主题一致。
// 由调用方 `openFor(info, x, y)` 弹出，`picked(action)` 回传动作。
import QtQuick
import "theme"

Rectangle {
    id: menu
    property bool open: false
    property string oid: ""
    property bool fav: false
    property bool arch: false
    property bool trashed: false
    signal picked(string action)

    visible: open
    width: 198
    height: col.implicitHeight + 10
    radius: CairnTheme.radius
    color: CairnTheme.elevated
    border.color: CairnTheme.borderStrong
    border.width: 1
    z: 200

    function openFor(info, x, y) {
        if (!info || info.oid === undefined || info.oid === "")
            return;
        menu.oid = info.oid;
        menu.fav = !!info.favorite;
        menu.arch = !!info.archived;
        menu.trashed = !!info.trashed;
        const m = CairnTheme.spaceSm;
        menu.x = Math.max(m, Math.min(x, parent.width - menu.width - m));
        menu.y = Math.max(m, Math.min(y, parent.height - menu.height - m));
        menu.open = true;
    }

    function close() {
        menu.open = false;
    }

    Column {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 5
        spacing: 1

        MenuRow {
            glyph: "\uE8A5"
            label: "打开"
            onTapped: menu.picked("open")
        }
        MenuRow {
            glyph: "\uE8F1"
            label: "复刻一份"
            onTapped: menu.picked("derive")
        }

        Sep {}

        MenuRow {
            glyph: menu.fav ? "\uE735" : "\uE734"
            label: menu.fav ? "取消收藏" : "收藏"
            onTapped: menu.picked("favorite")
        }
        MenuRow {
            glyph: "\uE7B8"
            label: menu.arch ? "取消归档" : "归档"
            onTapped: menu.picked("archive")
        }
        MenuRow {
            glyph: "\uE72E"
            label: "分享…"
            onTapped: menu.picked("share")
        }

        Sep {}

        MenuRow {
            glyph: "\uE81C"
            label: "历史版本"
            onTapped: menu.picked("history")
        }
        MenuRow {
            glyph: "\uE71B"
            label: "关系图"
            onTapped: menu.picked("relations")
        }

        Sep {}

        MenuRow {
            visible: !menu.trashed
            glyph: "\uE74D"
            label: "移到回收站"
            onTapped: menu.picked("trash")
        }
        MenuRow {
            visible: menu.trashed
            glyph: "\uE777"
            label: "恢复"
            onTapped: menu.picked("restore")
        }
        MenuRow {
            visible: menu.trashed
            glyph: "\uE74D"
            label: "彻底删除"
            danger: true
            onTapped: menu.picked("purge")
        }
    }

    component MenuRow: Rectangle {
        id: mr
        property string glyph: ""
        property string label: ""
        property bool danger: false
        signal tapped()
        width: parent.width
        height: 30
        radius: CairnTheme.radiusSm
        color: mrMa.containsMouse ? CairnTheme.hover : "transparent"
        Behavior on color {
            ColorAnimation {
                duration: CairnTheme.durFast
            }
        }
        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 10
            spacing: 9
            Text {
                width: 14
                anchors.verticalCenter: parent.verticalCenter
                text: mr.glyph
                font.family: CairnTheme.iconFont
                font.pixelSize: 12
                color: mr.danger ? CairnTheme.danger : CairnTheme.muted
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: mr.label
                color: mr.danger ? CairnTheme.danger : CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
        }
        MouseArea {
            id: mrMa
            anchors.fill: parent
            hoverEnabled: true
            onClicked: mr.tapped()
        }
    }

    component Sep: Rectangle {
        width: parent.width
        height: 1
        color: CairnTheme.border
        opacity: 0.7
    }
}
