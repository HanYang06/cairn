// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 通用小输入框（组口令等）。调用方 `ask(title, placeholder)`，`submitted(text)` / `cancelled()` 回传。
import QtQuick
import "theme"

Rectangle {
    id: box
    property bool open: false
    property string title: ""
    property string placeholder: ""
    property string error: ""
    property bool echoPassword: true
    signal submitted(string text)
    signal cancelled()

    visible: open
    width: 320
    height: content.implicitHeight + 32
    radius: CairnTheme.radiusLg
    color: CairnTheme.elevated
    border.color: CairnTheme.borderStrong
    border.width: 1
    z: 220

    function ask(titleText, placeholderText, password) {
        box.title = titleText;
        box.placeholder = placeholderText;
        box.echoPassword = password !== false;
        box.error = "";
        box.open = true;
        input.text = "";
        Qt.callLater(function () {
            input.forceActiveFocus();
        });
    }

    function close() {
        box.open = false;
    }

    function showError(message) {
        box.error = message;
        input.selectAll();
        input.forceActiveFocus();
    }

    Keys.onEscapePressed: {
        box.cancelled();
        box.close();
    }

    Column {
        id: content
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: CairnTheme.spaceLg
        spacing: CairnTheme.spaceSm

        Text {
            width: parent.width
            text: box.title
            color: CairnTheme.text
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsBody
            font.weight: Font.DemiBold
        }

        Rectangle {
            width: parent.width
            height: 30
            radius: CairnTheme.radiusSm
            color: CairnTheme.bg
            border.color: box.error !== "" ? CairnTheme.danger : (input.activeFocus ? CairnTheme.accent : CairnTheme.border)
            border.width: 1
            TextInput {
                id: input
                anchors.fill: parent
                anchors.leftMargin: 9
                anchors.rightMargin: 9
                verticalAlignment: TextInput.AlignVCenter
                clip: true
                echoMode: box.echoPassword ? TextInput.Password : TextInput.Normal
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
                selectByMouse: true
                onAccepted: box.submitted(input.text)
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    visible: input.text === ""
                    text: box.placeholder
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                }
            }
        }

        Text {
            width: parent.width
            visible: box.error !== ""
            text: box.error
            color: CairnTheme.danger
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
        }

        Row {
            spacing: CairnTheme.spaceSm
            anchors.right: parent.right
            Rectangle {
                width: 64
                height: 28
                radius: CairnTheme.radiusSm
                color: cancelMa.containsMouse ? CairnTheme.hover : "transparent"
                Text {
                    anchors.centerIn: parent
                    text: "取消"
                    color: CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                }
                MouseArea {
                    id: cancelMa
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: {
                        box.cancelled();
                        box.close();
                    }
                }
            }
            Rectangle {
                width: 64
                height: 28
                radius: CairnTheme.radiusSm
                color: CairnTheme.accent
                Text {
                    anchors.centerIn: parent
                    text: "确定"
                    color: CairnTheme.accentText
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    font.weight: Font.Medium
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: box.submitted(input.text)
                }
            }
        }
    }
}
