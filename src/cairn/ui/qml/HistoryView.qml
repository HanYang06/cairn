// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 版本历史：列表 + 预览 + 恢复。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: view
    color: CairnTheme.surface

    property int selected: -1
    property string previewText: ""

    function selectVersion(seq) {
        view.selected = seq;
        view.previewText = backend.previewVersion(seq);
    }

    Connections {
        target: backend
        function onViewChanged() {
            view.selected = -1;
            view.previewText = "";
        }
        function onVersionsChanged() {
            view.previewText = backend.previewVersion(view.selected);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            color: CairnTheme.bg
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: CairnTheme.border
                opacity: 0.6
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceMd
                spacing: CairnTheme.spaceSm
                Text {
                    text: "\uE81C"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 13
                    color: CairnTheme.borderStrong
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: "历史"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    font.weight: Font.DemiBold
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: backend.historyTitle !== "" ? ("· " + backend.historyTitle) : ""
                    color: CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    Layout.alignment: Qt.AlignVCenter
                }
                Item {
                    Layout.fillWidth: true
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Flickable {
                Layout.preferredWidth: 280
                Layout.fillHeight: true
                clip: true
                contentHeight: versionColumn.height

                Column {
                    id: versionColumn
                    width: parent.width
                    Repeater {
                        model: backend.currentVersions
                        delegate: Rectangle {
                            width: versionColumn.width
                            height: 56
                            color: view.selected === modelData.seq ? CairnTheme.selection : (verMa.containsMouse ? CairnTheme.hover : "transparent")
                            Rectangle {
                                width: 2
                                height: parent.height
                                color: CairnTheme.accent
                                opacity: view.selected === modelData.seq ? 1 : 0
                            }
                            Column {
                                anchors.left: parent.left
                                anchors.leftMargin: CairnTheme.spaceMd
                                anchors.right: parent.right
                                anchors.rightMargin: CairnTheme.spaceMd
                                anchors.verticalCenter: parent.verticalCenter
                                spacing: 3
                                RowLayout {
                                    width: parent.width
                                    Text {
                                        text: "#" + modelData.seq
                                        color: CairnTheme.text
                                        font.family: CairnTheme.fontFamily
                                        font.pixelSize: CairnTheme.fsSmall
                                        font.weight: Font.Medium
                                        Layout.fillWidth: true
                                    }
                                    Text {
                                        visible: modelData.current
                                        text: "当前"
                                        color: CairnTheme.accent
                                        font.family: CairnTheme.fontFamily
                                        font.pixelSize: CairnTheme.fsTiny
                                    }
                                }
                                Text {
                                    text: modelData.updated + " · " + modelData.size
                                    color: CairnTheme.muted
                                    font.family: CairnTheme.fontFamily
                                    font.pixelSize: CairnTheme.fsTiny
                                }
                            }
                            MouseArea {
                                id: verMa
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: view.selectVersion(modelData.seq)
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.preferredWidth: 1
                Layout.fillHeight: true
                color: CairnTheme.border
                opacity: 0.5
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                Item {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.margins: CairnTheme.spaceLg
                    Text {
                        anchors.fill: parent
                        visible: view.selected >= 0
                        text: view.previewText !== "" ? view.previewText : "（空）"
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsBody
                        wrapMode: Text.Wrap
                    }
                    Text {
                        anchors.centerIn: parent
                        visible: view.selected < 0
                        text: "选择左侧版本查看内容"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 46
                    visible: view.selected >= 0 && !isCurrent(view.selected)
                    color: CairnTheme.bg
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: CairnTheme.spaceLg
                        anchors.rightMargin: CairnTheme.spaceLg
                        Item {
                            Layout.fillWidth: true
                        }
                        Rectangle {
                            Layout.alignment: Qt.AlignVCenter
                            width: restoreLabel.implicitWidth + 28
                            height: 30
                            radius: CairnTheme.radius
                            color: restoreMa.containsMouse ? CairnTheme.selection : CairnTheme.bg
                            border.color: CairnTheme.accent
                            border.width: 1
                            Text {
                                id: restoreLabel
                                anchors.centerIn: parent
                                text: "恢复此版本"
                                color: CairnTheme.accent
                                font.family: CairnTheme.fontFamily
                                font.pixelSize: CairnTheme.fsTiny
                                font.weight: Font.Medium
                            }
                            MouseArea {
                                id: restoreMa
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: backend.restoreVersion(view.selected)
                            }
                        }
                    }
                }
            }
        }
    }

    function isCurrent(seq) {
        const versions = backend.currentVersions;
        for (let i = 0; i < versions.length; i++) {
            if (versions[i].seq === seq)
                return versions[i].current;
        }
        return false;
    }
}
