// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 分享弹层：独立于属性区的一等动作。
// 上：公开到个人主页（开关）；下：直接列出可分享的社区 / 成员（点击即切换），不手输。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: pop
    property bool open: false
    signal closed()

    readonly property var shares: backend.currentShares
    readonly property var communities: backend.shareTargets.filter(function (t) {
        return t.kind === "community";
    })
    readonly property var people: backend.shareTargets.filter(function (t) {
        return t.kind === "person";
    })

    function isShared(kind, name) {
        return shares.some(function (s) {
            return s.kind === kind && s.name === name;
        });
    }

    function hasHomepage() {
        return shares.some(function (s) {
            return s.kind === "homepage";
        });
    }

    function openAt(x, y) {
        const m = CairnTheme.spaceSm;
        pop.x = Math.max(m, Math.min(x, parent.width - pop.width - m));
        pop.y = Math.max(m, Math.min(y, parent.height - pop.height - m));
        pop.open = true;
    }

    function close() {
        pop.open = false;
    }

    visible: open
    width: 292
    height: col.implicitHeight + 20
    radius: CairnTheme.radius
    color: CairnTheme.elevated
    border.color: CairnTheme.borderStrong
    border.width: 1
    z: 200

    ColumnLayout {
        id: col
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 10
        spacing: CairnTheme.spaceSm

        RowLayout {
            Layout.fillWidth: true
            Text {
                text: "分享"
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
                font.weight: Font.DemiBold
                Layout.fillWidth: true
            }
            Text {
                text: "\uE8BB"
                font.family: CairnTheme.iconFont
                font.pixelSize: 10
                color: CairnTheme.faint
                MouseArea {
                    anchors.fill: parent
                    anchors.margins: -6
                    onClicked: pop.close()
                }
            }
        }

        // 公开到个人主页：语义上是开关，不属于「分享给」。
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 30
            radius: CairnTheme.radiusSm
            color: pop.hasHomepage() ? CairnTheme.selection : CairnTheme.hover
            Text {
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                text: "公开到个人主页"
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
            Text {
                anchors.right: parent.right
                anchors.rightMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                visible: pop.hasHomepage()
                text: "已公开"
                color: CairnTheme.accent
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: backend.toggleHomepage()
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 1
            color: CairnTheme.borderFaint
        }

        Text {
            Layout.leftMargin: 2
            text: "分享给"
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.weight: Font.DemiBold
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: pop.communities
                delegate: TargetChip {
                    target: modelData
                }
            }
        }

        Flow {
            Layout.fillWidth: true
            spacing: 6
            visible: pop.people.length > 0
            Repeater {
                model: pop.people
                delegate: TargetChip {
                    target: modelData
                }
            }
        }

        Text {
            Layout.leftMargin: 2
            visible: pop.communities.length === 0 && pop.people.length === 0
            text: "暂无可分享对象"
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
        }
    }

    component TargetChip: Rectangle {
        id: chip
        property var target
        readonly property bool shared: pop.isShared(target.kind, target.name)
        width: chipRow.implicitWidth + 20
        height: 26
        radius: 13
        color: (chip.shared || chipMa.containsMouse) ? CairnTheme.selection : CairnTheme.hover
        border.color: chip.shared ? CairnTheme.accent : "transparent"
        border.width: 1
        Row {
            id: chipRow
            anchors.centerIn: parent
            spacing: 4
            Text {
                anchors.verticalCenter: parent.verticalCenter
                text: chip.target.name
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
            Text {
                anchors.verticalCenter: parent.verticalCenter
                visible: chip.shared
                text: "\uE73E"
                font.family: CairnTheme.iconFont
                font.pixelSize: 9
                color: CairnTheme.accent
            }
        }
        MouseArea {
            id: chipMa
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: backend.toggleShareTo(chip.target.kind, chip.target.name)
        }
    }
}
