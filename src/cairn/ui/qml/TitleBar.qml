// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: bar
    color: CairnTheme.chrome

    MouseArea {
        id: dragArea
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        property point pressPos
        property point winPos
        onPressed: {
            if (Window.window) {
                pressPos = Qt.point(mouse.x, mouse.y);
                winPos = Qt.point(Window.window.x, Window.window.y);
            }
        }
        onPositionChanged: {
            if (pressed && Window.window) {
                Window.window.x = winPos.x + (mouse.x - pressPos.x);
                Window.window.y = winPos.y + (mouse.y - pressPos.y);
            }
        }
        onDoubleClicked: {
            if (!Window.window)
                return;
            if (Window.window.visibility === Window.Maximized)
                Window.window.showNormal();
            else
                Window.window.showMaximized();
        }
    }

    Rectangle {
        anchors.bottom: parent.bottom
        width: parent.width
        height: 1
        color: CairnTheme.bg
    }

    RowLayout {
        anchors.fill: parent
        anchors.leftMargin: CairnTheme.spaceMd
        spacing: CairnTheme.spaceSm

        Column {
            Layout.alignment: Qt.AlignVCenter
            spacing: 1
            Repeater {
                model: [12, 16, 9]
                Rectangle {
                    width: modelData
                    height: 3
                    radius: 1.5
                    color: CairnTheme.accent
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }

        Text {
            text: "Cairn"
            color: CairnTheme.text
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsSmall
            font.weight: Font.DemiBold
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: "/"
            color: CairnTheme.faint
            font.pixelSize: CairnTheme.fsSmall
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: "个人空间"
            color: CairnTheme.muted
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsSmall
            Layout.alignment: Qt.AlignVCenter
        }
        Text {
            text: "\uE72E"
            font.family: CairnTheme.iconFont
            font.pixelSize: 10
            color: CairnTheme.faint
            Layout.alignment: Qt.AlignVCenter
        }

        Item {
            Layout.fillWidth: true
        }

        Row {
            Layout.alignment: Qt.AlignTop
            WindowButton {
                glyph: "\uE921"
                onClicked: {
                    if (Window.window)
                        Window.window.showMinimized();
                }
            }
            WindowButton {
                glyph: "\uE922"
                onClicked: {
                    if (!Window.window)
                        return;
                    if (Window.window.visibility === Window.Maximized)
                        Window.window.showNormal();
                    else
                        Window.window.showMaximized();
                }
            }
            WindowButton {
                glyph: "\uE8BB"
                hoverColor: CairnTheme.danger
                hoverFg: "#FFFFFF"
                onClicked: {
                    if (Window.window)
                        Window.window.close();
                }
            }
        }
    }

    component WindowButton: Rectangle {
        id: wb
        property string glyph
        property color hoverColor: CairnTheme.hover
        property color hoverFg: CairnTheme.text
        signal clicked()
        width: 46
        height: CairnTheme.titleBarH
        color: wbMa.containsMouse ? wb.hoverColor : "transparent"
        Behavior on color {
            ColorAnimation {
                duration: CairnTheme.durFast
            }
        }
        Text {
            anchors.centerIn: parent
            text: wb.glyph
            font.family: CairnTheme.iconFont
            font.pixelSize: 10
            color: wbMa.containsMouse ? wb.hoverFg : CairnTheme.muted
        }
        MouseArea {
            id: wbMa
            anchors.fill: parent
            hoverEnabled: true
            onClicked: wb.clicked()
        }
    }
}
