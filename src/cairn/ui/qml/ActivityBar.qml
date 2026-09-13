// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: bar
    color: CairnTheme.chrome

    property int current: 0
    signal activated(int index)

    property var domains: [
        {
            "kind": "notes",
            "label": "笔记"
        },
        {
            "kind": "projects",
            "label": "项目"
        },
        {
            "kind": "community",
            "label": "社区"
        },
        {
            "kind": "graph",
            "label": "图谱"
        },
        {
            "kind": "search",
            "glyph": "\uE721",
            "label": "搜索"
        },
        {
            "kind": "tags",
            "glyph": "\uE8EC",
            "label": "标签"
        },
        {
            "kind": "assets",
            "glyph": "\uE91B",
            "label": "资产"
        }
    ]

    ColumnLayout {
        anchors.fill: parent
        anchors.topMargin: CairnTheme.spaceSm
        anchors.bottomMargin: CairnTheme.spaceSm
        spacing: 0

        Repeater {
            model: bar.domains
            delegate: RailButton {
                Layout.alignment: Qt.AlignHCenter
                kind: modelData.kind
                glyph: modelData.glyph || ""
                active: index === bar.current
                onClicked: bar.activated(index)
            }
        }

        Item {
            Layout.fillHeight: true
        }

        // 头像在上
        Item {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 34
            Layout.preferredHeight: 34
            Rectangle {
                id: avatar
                anchors.centerIn: parent
                width: 28
                height: 28
                radius: 14
                color: avatarMa.containsMouse ? CairnTheme.accent : CairnTheme.elevated
                border.color: CairnTheme.accent
                border.width: 1
                Behavior on color {
                    ColorAnimation {
                        duration: CairnTheme.durFast
                    }
                }
                Text {
                    anchors.centerIn: parent
                    text: "韩"
                    color: avatarMa.containsMouse ? CairnTheme.accentText : CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: 12
                    font.weight: Font.DemiBold
                }
                MouseArea {
                    id: avatarMa
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
        }

        Item {
            Layout.preferredHeight: CairnTheme.spaceXs
        }

        // 设置在最底
        RailButton {
            Layout.alignment: Qt.AlignHCenter
            kind: "settings"
            glyph: "\uE713"
        }
    }

    component RailButton: Item {
        id: rb
        property string kind: ""
        property string glyph: ""
        property bool active: false
        signal clicked()
        readonly property color ink: active || rbMa.containsMouse ? CairnTheme.text : CairnTheme.muted

        Layout.preferredWidth: 40
        Layout.preferredHeight: 40

        Rectangle {
            width: 2
            height: 20
            radius: 1
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            color: CairnTheme.accent
            opacity: rb.active ? 1 : 0
            Behavior on opacity {
                NumberAnimation {
                    duration: CairnTheme.durFast
                }
            }
        }
        Rectangle {
            anchors.fill: parent
            anchors.margins: 5
            radius: CairnTheme.radiusSm
            color: rbMa.containsMouse && !rb.active ? CairnTheme.hover : "transparent"
            Behavior on color {
                ColorAnimation {
                    duration: CairnTheme.durFast
                }
            }
        }

        // —— 领域 Logo（自绘）——
        // 笔记：书本
        Item {
            visible: rb.kind === "notes"
            anchors.centerIn: parent
            width: 15
            height: 17
            Rectangle {
                anchors.fill: parent
                radius: 2
                color: "transparent"
                border.color: rb.ink
                border.width: 1.4
            }
            Rectangle {
                x: 3
                width: 1.3
                height: parent.height
                color: rb.ink
            }
            Rectangle {
                x: 6
                y: 5
                width: 6
                height: 1.3
                radius: 0.6
                color: rb.ink
            }
            Rectangle {
                x: 6
                y: 9
                width: 4
                height: 1.3
                radius: 0.6
                color: rb.ink
            }
        }
        // 项目：仓库（书本 + 书签，参考 GitHub Repo）
        Item {
            visible: rb.kind === "projects"
            anchors.centerIn: parent
            width: 15
            height: 17
            Rectangle {
                anchors.fill: parent
                radius: 2
                color: "transparent"
                border.color: rb.ink
                border.width: 1.4
            }
            Rectangle {
                x: 3
                width: 1.3
                height: parent.height
                color: rb.ink
            }
            Rectangle {
                x: 8
                y: 1
                width: 4
                height: 6
                radius: 1
                color: rb.ink
            }
        }
        // 社区：四点成组
        Item {
            visible: rb.kind === "community"
            anchors.centerIn: parent
            width: 18
            height: 18
            Repeater {
                model: [[5, 5], [13, 5], [5, 13], [13, 13]]
                Rectangle {
                    width: 7
                    height: 7
                    radius: 3.5
                    color: rb.ink
                    x: modelData[0] - 3.5
                    y: modelData[1] - 3.5
                }
            }
        }
        // 图谱：三点连线
        Canvas {
            id: graphIcon
            visible: rb.kind === "graph"
            anchors.centerIn: parent
            width: 18
            height: 18
            onPaint: {
                const ctx = getContext("2d");
                ctx.reset();
                ctx.strokeStyle = rb.ink;
                ctx.fillStyle = rb.ink;
                ctx.lineWidth = 1.4;
                const p = [[9, 3], [3, 15], [15, 15]];
                ctx.beginPath();
                ctx.moveTo(p[0][0], p[0][1]);
                ctx.lineTo(p[1][0], p[1][1]);
                ctx.moveTo(p[0][0], p[0][1]);
                ctx.lineTo(p[2][0], p[2][1]);
                ctx.moveTo(p[1][0], p[1][1]);
                ctx.lineTo(p[2][0], p[2][1]);
                ctx.stroke();
                for (let i = 0; i < 3; i++) {
                    ctx.beginPath();
                    ctx.arc(p[i][0], p[i][1], 2.6, 0, 7);
                    ctx.fill();
                }
            }
        }
        // 其余用字形
        Text {
            visible: rb.kind !== "notes" && rb.kind !== "projects" && rb.kind !== "community" && rb.kind !== "graph"
            anchors.centerIn: parent
            text: rb.glyph
            font.family: CairnTheme.iconFont
            font.pixelSize: 16
            color: rb.ink
        }

        MouseArea {
            id: rbMa
            anchors.fill: parent
            hoverEnabled: true
            onClicked: rb.clicked()
        }
    }
}
