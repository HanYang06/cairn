// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 底部状态栏：可见性 + 谱系面包屑 + 作者/时间。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: status
    color: CairnTheme.chrome

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
            text: backend.currentVisibility + " · 已解锁"
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

        RowLayout {
            Layout.fillWidth: true
            spacing: 6
            Repeater {
                model: backend.currentPath
                delegate: Row {
                    spacing: 6
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: index > 0
                        text: ">"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        font.weight: Font.DemiBold
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.title
                        color: modelData.current ? CairnTheme.accent : CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        font.weight: modelData.current ? Font.DemiBold : Font.Normal
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
            text: backend.currentAuthor
            color: CairnTheme.muted
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: backend.currentUpdated
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            Layout.alignment: Qt.AlignVCenter
        }
    }
}
