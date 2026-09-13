// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 档案菜单：切换/新建本地档案（昵称）。设备身份在库里，这里只是表层名字。
import QtQuick
import QtQuick.Layouts
import "theme"

Item {
    id: menu
    clip: true
    property bool open: false
    signal closed()

    implicitWidth: 240
    implicitHeight: 232

    Rectangle {
        id: panel
        width: menu.width
        height: menu.height
        y: menu.open ? 0 : menu.height + 8
        radius: CairnTheme.radiusLg
        color: CairnTheme.elevated
        border.color: CairnTheme.borderStrong
        border.width: 1
        visible: menu.open
        Behavior on y {
            NumberAnimation {
                duration: CairnTheme.durBase
                easing.type: Easing.OutCubic
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: CairnTheme.spaceMd
            spacing: CairnTheme.spaceSm

            RowLayout {
                Layout.fillWidth: true
                Text {
                    text: "档案"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                Text {
                    text: "设备身份 · 单机"
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                }
            }

            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                contentHeight: profileColumn.height
                Column {
                    id: profileColumn
                    width: parent.width
                    spacing: 2
                    Repeater {
                        model: backend.profiles
                        delegate: Rectangle {
                            width: profileColumn.width
                            height: 30
                            radius: CairnTheme.radiusSm
                            color: modelData === backend.currentProfile ? CairnTheme.selection : (pMa.containsMouse ? CairnTheme.hover : "transparent")
                            Text {
                                anchors.left: parent.left
                                anchors.leftMargin: CairnTheme.spaceSm
                                anchors.verticalCenter: parent.verticalCenter
                                text: modelData
                                color: CairnTheme.text
                                font.family: CairnTheme.fontFamily
                                font.pixelSize: CairnTheme.fsSmall
                            }
                            Text {
                                anchors.right: parent.right
                                anchors.rightMargin: CairnTheme.spaceSm
                                anchors.verticalCenter: parent.verticalCenter
                                visible: modelData === backend.currentProfile
                                text: "\uE73E"
                                font.family: CairnTheme.iconFont
                                font.pixelSize: 11
                                color: CairnTheme.accent
                            }
                            MouseArea {
                                id: pMa
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: {
                                    backend.switchProfile(modelData);
                                    menu.closed();
                                }
                            }
                        }
                    }
                    Text {
                        visible: backend.profiles.length === 0
                        text: "还没有档案"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 30
                radius: CairnTheme.radiusSm
                color: CairnTheme.bg
                border.color: nameInput.activeFocus ? CairnTheme.accent : CairnTheme.border
                border.width: 1
                TextInput {
                    id: nameInput
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    verticalAlignment: TextInput.AlignVCenter
                    clip: true
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    selectByMouse: true
                    onAccepted: {
                        backend.createProfile(nameInput.text);
                        nameInput.text = "";
                        menu.closed();
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: nameInput.text === ""
                        text: "新建档案，回车…"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                    }
                }
            }
        }
    }
}
