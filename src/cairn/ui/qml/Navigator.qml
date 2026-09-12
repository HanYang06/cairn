// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 双态导航：mode = "notes"（笔记写法）| "projects"（仓库形式）。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: nav
    color: CairnTheme.surface
    property string mode: "notes"

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: CairnTheme.border
        opacity: 0.6
    }

    // ============ 笔记导航 ============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "notes"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: "笔记"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                IconGlyph {
                    glyph: "\uE710"
                }
                IconGlyph {
                    glyph: "\uE712"
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: CairnTheme.spaceMd
            Layout.rightMargin: CairnTheme.spaceMd
            Layout.preferredHeight: 32
            radius: CairnTheme.radiusSm
            color: CairnTheme.bg
            border.color: CairnTheme.border
            border.width: 1
            Text {
                x: 9
                anchors.verticalCenter: parent.verticalCenter
                text: "\uE70F"
                font.family: CairnTheme.iconFont
                font.pixelSize: 12
                color: CairnTheme.accent
            }
            Text {
                x: 28
                anchors.verticalCenter: parent.verticalCenter
                text: "快速记录…"
                color: CairnTheme.faint
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
            }
        }

        Item {
            Layout.preferredHeight: CairnTheme.spaceMd
        }

        Text {
            Layout.leftMargin: CairnTheme.spaceMd
            text: "结构"
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.weight: Font.DemiBold
            font.letterSpacing: 0.6
        }

        ListView {
            id: treeList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            model: [
                {
                    "t": "未整理",
                    "lvl": 0,
                    "badge": "3",
                    "kind": "inbox"
                },
                {
                    "t": "石堆设计笔记",
                    "lvl": 0,
                    "open": true,
                    "kind": "note"
                },
                {
                    "t": "布局取舍 v1",
                    "lvl": 1,
                    "kind": "note"
                },
                {
                    "t": "QML 外壳草案",
                    "lvl": 1,
                    "kind": "note"
                },
                {
                    "t": "存储层设计笔记",
                    "lvl": 0,
                    "kind": "note"
                },
                {
                    "t": "MCP 作为 AI 接入面",
                    "lvl": 0,
                    "kind": "note"
                },
                {
                    "t": "设计灵感/交互参考",
                    "lvl": 0,
                    "kind": "note"
                }
            ]
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                id: node
                width: treeList.width
                height: 30
                color: nodeMa.containsMouse ? CairnTheme.hover : "transparent"

                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    x: CairnTheme.spaceSm + modelData.lvl * CairnTheme.spaceLg
                    spacing: 6
                    Text {
                        visible: modelData.lvl === 0 && modelData.open !== undefined
                        text: "\uE70D"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 8
                        color: CairnTheme.faint
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: modelData.kind === "inbox" ? "\uE715" : "\uE8A5"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 12
                        color: modelData.kind === "inbox" ? CairnTheme.accent : CairnTheme.muted
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: modelData.t
                        color: modelData.lvl === 0 ? CairnTheme.text : CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }
                Rectangle {
                    visible: modelData.badge !== undefined
                    anchors.right: parent.right
                    anchors.rightMargin: CairnTheme.spaceMd
                    anchors.verticalCenter: parent.verticalCenter
                    width: 18
                    height: 18
                    radius: 9
                    color: CairnTheme.accent
                    Text {
                        anchors.centerIn: parent
                        text: modelData.badge || ""
                        color: CairnTheme.accentText
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: 10
                        font.weight: Font.DemiBold
                    }
                }
                MouseArea {
                    id: nodeMa
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
        }
    }

    // ============ 项目导航（仓库形式）============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "projects"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: "项目"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                IconGlyph {
                    glyph: "\uE710"
                }
                IconGlyph {
                    glyph: "\uE712"
                }
            }
        }

        ListView {
            id: repoList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            spacing: 2
            model: [
                {
                    "name": "Cairn 客户端",
                    "line": "main · 活跃 · 24 节点",
                    "state": "active"
                },
                {
                    "name": "石堆设计",
                    "line": "draft · 8 节点",
                    "state": "draft"
                },
                {
                    "name": "个人知识库",
                    "line": "main · 归档 · 132 节点",
                    "state": "idle"
                },
                {
                    "name": "论文：本地优先",
                    "line": "reading · 41 节点",
                    "state": "active"
                }
            ]
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                width: repoList.width - CairnTheme.spaceMd * 2
                x: CairnTheme.spaceMd
                height: 58
                radius: CairnTheme.radius
                color: repoMa.containsMouse ? CairnTheme.hover : "transparent"
                Behavior on color {
                    ColorAnimation {
                        duration: CairnTheme.durFast
                    }
                }

                Rectangle {
                    id: repoIcon
                    width: 30
                    height: 30
                    radius: CairnTheme.radiusSm
                    anchors.left: parent.left
                    anchors.leftMargin: 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: CairnTheme.elevated
                    Text {
                        anchors.centerIn: parent
                        text: "\uE8B7"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 14
                        color: CairnTheme.accent
                    }
                }
                Column {
                    anchors.left: repoIcon.right
                    anchors.leftMargin: CairnTheme.spaceSm
                    anchors.right: stateDot.left
                    anchors.rightMargin: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text {
                        text: modelData.name
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        font.weight: Font.Medium
                        width: parent.width
                        elide: Text.ElideRight
                    }
                    Text {
                        text: modelData.line
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        width: parent.width
                        elide: Text.ElideRight
                    }
                }
                Rectangle {
                    id: stateDot
                    width: 6
                    height: 6
                    radius: 3
                    anchors.right: parent.right
                    anchors.rightMargin: 4
                    anchors.top: parent.top
                    anchors.topMargin: CairnTheme.spaceSm
                    color: modelData.state === "active" ? CairnTheme.accentAlt : CairnTheme.faint
                }
                MouseArea {
                    id: repoMa
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
        }
    }

    // ============ 社区导航 ============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "community"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: "社区"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                IconGlyph {
                    glyph: "\uE710"
                }
                IconGlyph {
                    glyph: "\uE712"
                }
            }
        }

        ListView {
            id: communityList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            spacing: 2
            model: [
                {
                    "name": "Cairn 中文",
                    "line": "1,204 成员 · 12 版块",
                    "state": "active"
                },
                {
                    "name": "本地优先软件",
                    "line": "560 成员 · 6 版块",
                    "state": "active"
                },
                {
                    "name": "开源设计",
                    "line": "318 成员 · 4 版块",
                    "state": "idle"
                }
            ]
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                width: communityList.width - CairnTheme.spaceMd * 2
                x: CairnTheme.spaceMd
                height: 58
                radius: CairnTheme.radius
                color: commMa.containsMouse ? CairnTheme.hover : "transparent"
                Behavior on color {
                    ColorAnimation {
                        duration: CairnTheme.durFast
                    }
                }

                Rectangle {
                    id: commIcon
                    width: 30
                    height: 30
                    radius: 15
                    anchors.left: parent.left
                    anchors.leftMargin: 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: CairnTheme.elevated
                    border.color: CairnTheme.border
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: "\uE716"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 14
                        color: CairnTheme.accent
                    }
                }
                Column {
                    anchors.left: commIcon.right
                    anchors.leftMargin: CairnTheme.spaceSm
                    anchors.right: parent.right
                    anchors.rightMargin: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text {
                        text: modelData.name
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        font.weight: Font.Medium
                        width: parent.width
                        elide: Text.ElideRight
                    }
                    Text {
                        text: modelData.line
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        width: parent.width
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    id: commMa
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
        }
    }

    component IconGlyph: Item {
        id: ig
        property string glyph
        Layout.preferredWidth: 26
        Layout.preferredHeight: 26
        Rectangle {
            anchors.fill: parent
            radius: CairnTheme.radiusSm
            color: igMa.containsMouse ? CairnTheme.hover : "transparent"
            Behavior on color {
                ColorAnimation {
                    duration: CairnTheme.durFast
                }
            }
        }
        Text {
            anchors.centerIn: parent
            text: ig.glyph
            font.family: CairnTheme.iconFont
            font.pixelSize: 13
            color: igMa.containsMouse ? CairnTheme.text : CairnTheme.muted
        }
        MouseArea {
            id: igMa
            anchors.fill: parent
            hoverEnabled: true
        }
    }
}
