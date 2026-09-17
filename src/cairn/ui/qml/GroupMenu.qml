// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 组的右键菜单：自绘，与主题一致。调用方 `openFor(info, x, y)`，`picked(action)` 回传。
import QtQuick
import "theme"

Rectangle {
    id: menu
    property bool open: false
    property string gid: ""
    property string title: ""
    property bool locked: false
    property bool hasKey: false
    property bool unlocked: true
    property bool inGroup: false
    signal picked(string action)

    visible: open
    width: 186
    height: col.implicitHeight + 10
    radius: CairnTheme.radius
    color: CairnTheme.elevated
    border.color: CairnTheme.borderStrong
    border.width: 1
    z: 200

    function openFor(info, x, y) {
        if (!info || !info.gid)
            return;
        menu.gid = info.gid;
        menu.title = info.title;
        menu.locked = !!info.lock;
        menu.hasKey = !!info.has_key;
        menu.unlocked = info.unlocked !== false;
        menu.inGroup = !!info.in_group;
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
            glyph: "\uE710"
            label: "加入当前笔记"
            onTapped: menu.picked("add")
        }
        MenuRow {
            glyph: "\uE721"
            label: "只看此组"
            onTapped: menu.picked("filter")
        }

        Sep {}

        MenuRow {
            glyph: "\uE74A"
            label: "上移"
            onTapped: menu.picked("up")
        }
        MenuRow {
            glyph: "\uE74B"
            label: "下移"
            onTapped: menu.picked("down")
        }
        MenuRow {
            visible: menu.inGroup
            glyph: "\uE8F4"
            label: "移出父组"
            onTapped: menu.picked("ungroup")
        }

        Sep {}

        MenuRow {
            glyph: "\uE72E"
            label: menu.hasKey ? "修改密码…" : "设置密码…"
            onTapped: menu.picked("key")
        }
        MenuRow {
            visible: menu.hasKey
            glyph: "\uE8D7"
            label: "清除密码"
            onTapped: menu.picked("clearkey")
        }
        MenuRow {
            glyph: menu.locked ? "\uE785" : "\uE72E"
            label: menu.locked ? "解锁组" : "锁定组"
            onTapped: menu.picked("lock")
        }

        Sep {}

        MenuRow {
            glyph: "\uE74D"
            label: "删除组"
            danger: true
            onTapped: menu.picked("delete")
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
