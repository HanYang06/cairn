// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 底部状态栏：以面包屑形式展示当前内容的谱系/演变路径。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: status
    color: CairnTheme.chrome

    property var crumb: [
        {
            "kind": "node",
            "t": "石堆设计笔记"
        },
        {
            "kind": "edge",
            "t": "派生"
        },
        {
            "kind": "node",
            "t": "布局取舍 v1"
        },
        {
            "kind": "edge",
            "t": "派生"
        },
        {
            "kind": "node",
            "t": "QML 外壳草案",
            "current": true
        }
    ]

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: CairnTheme.spaceMd
        anchors.rightMargin: CairnTheme.spaceMd
        spacing: CairnTheme.spaceSm

        Text {
            text: "\uE72E"
            font.family: CairnTheme.iconFont
            font.pixelSize: 10
            color: CairnTheme.accentAlt
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: "私密 · 已解锁"
            color: CairnTheme.muted
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            Layout.alignment: Qt.AlignVCenter
        }

        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            width: 1
            height: 12
            color: CairnTheme.border
        }

        // 谱系面包屑
        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: status.crumb
                delegate: Item {
                    Layout.alignment: Qt.AlignVCenter
                    implicitWidth: content.implicitWidth
                    implicitHeight: 16
                    Row {
                        id: content
                        spacing: 6
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: modelData.kind === "edge"
                            text: "─" + modelData.t + "→"
                            color: CairnTheme.faint
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            visible: modelData.kind === "node"
                            text: modelData.t
                            color: modelData.current ? CairnTheme.accent : CairnTheme.muted
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                            font.weight: modelData.current ? Font.DemiBold : Font.Normal
                        }
                    }
                }
            }
        }

        Rectangle {
            Layout.alignment: Qt.AlignVCenter
            width: 1
            height: 12
            color: CairnTheme.border
        }

        Text {
            text: "个人调整 · 09:12"
            color: CairnTheme.muted
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: "AI 就绪"
            color: CairnTheme.accentAlt
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            Layout.alignment: Qt.AlignVCenter
        }
    }
}
