// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: area
    color: CairnTheme.surface

    function tabActive(key, kind) {
        if (kind === "note")
            return backend.currentView === "note" && key === backend.currentOid;
        if (kind === "relations")
            return backend.currentView === "relations";
        if (kind === "history")
            return backend.currentView === "history" && key === ("history:" + backend.historyOid);
        return false;
    }

    function kindColor(kind) {
        if (kind === "relations")
            return CairnTheme.accentAlt;
        if (kind === "history")
            return CairnTheme.borderStrong;
        return CairnTheme.accent;
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: CairnTheme.tabBarH
            color: CairnTheme.bg

            Row {
                anchors.fill: parent
                Repeater {
                    model: tabsModel
                    delegate: Rectangle {
                        id: tab
                        readonly property bool active: area.tabActive(model.oid, model.kind)
                        width: Math.min(220, Math.max(130, tabText.implicitWidth + 64))
                        height: parent.height
                        color: tab.active ? CairnTheme.surface : (tabMa.containsMouse ? CairnTheme.hover : "transparent")
                        Behavior on color {
                            ColorAnimation {
                                duration: CairnTheme.durFast
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 2
                            color: CairnTheme.accent
                            opacity: tab.active ? 1 : 0
                            Behavior on opacity {
                                NumberAnimation {
                                    duration: CairnTheme.durFast
                                }
                            }
                        }
                        Rectangle {
                            width: 1
                            height: parent.height - 18
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter
                            color: CairnTheme.border
                            opacity: 0.5
                        }
                        Rectangle {
                            x: CairnTheme.spaceMd
                            anchors.verticalCenter: parent.verticalCenter
                            width: 6
                            height: 6
                            radius: 3
                            color: area.kindColor(model.kind)
                        }
                        Text {
                            id: tabText
                            anchors.left: parent.left
                            anchors.leftMargin: 26
                            anchors.right: closeBtn.left
                            anchors.rightMargin: 4
                            anchors.verticalCenter: parent.verticalCenter
                            text: model.title
                            color: tab.active ? CairnTheme.text : CairnTheme.muted
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsSmall
                            elide: Text.ElideRight
                        }
                        Item {
                            id: closeBtn
                            z: 2
                            anchors.right: parent.right
                            anchors.rightMargin: 8
                            anchors.verticalCenter: parent.verticalCenter
                            width: 18
                            height: 18
                            Rectangle {
                                anchors.fill: parent
                                radius: 4
                                color: closeMa.containsMouse ? CairnTheme.hover : "transparent"
                            }
                            Text {
                                anchors.centerIn: parent
                                text: "\uE8BB"
                                font.family: CairnTheme.iconFont
                                font.pixelSize: 9
                                color: CairnTheme.faint
                            }
                            MouseArea {
                                id: closeMa
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: backend.closeTab(model.oid)
                            }
                        }
                        MouseArea {
                            id: tabMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: backend.activateTab(model.oid)
                        }
                    }
                }
            }
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: CairnTheme.border
                opacity: 0.4
            }
        }

        NoteEditor {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: backend.currentView === "note" && backend.currentOid !== ""
        }
        EmptyState {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: backend.currentView === "note" && backend.currentOid === ""
        }
        RelationsView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: backend.currentView === "relations"
        }
        HistoryView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: backend.currentView === "history"
        }
    }

    component NoteEditor: Item {
        id: ed
        property bool loading: true
        property string status: ""

        Component.onCompleted: loading = false

        Connections {
            target: backend
            function onCurrentChanged() {
                ed.loading = true;
                titleInput.text = backend.currentTitle;
                body.text = backend.currentText;
                ed.loading = false;
                ed.status = "";
            }
            function onContentChanged() {
                ed.status = "已保存";
            }
        }

        Flickable {
            id: flick
            anchors.fill: parent
            contentWidth: width
            contentHeight: col.height + 64
            clip: true

            Column {
                id: col
                width: Math.min(flick.width - 72, 720)
                x: Math.max(36, (flick.width - width) / 2)
                y: 28
                spacing: CairnTheme.spaceMd

                TextInput {
                    id: titleInput
                    width: parent.width
                    text: backend.currentTitle
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTitle
                    font.weight: Font.DemiBold
                    selectByMouse: true
                    clip: true
                    onEditingFinished: backend.renameNote(text)
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: titleInput.text === ""
                        text: "无标题"
                        color: CairnTheme.faint
                        font: titleInput.font
                    }
                }

                Row {
                    height: 18
                    spacing: CairnTheme.spaceSm
                    Text {
                        text: "笔记"
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    Text {
                        text: "·"
                        color: CairnTheme.faint
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    Text {
                        text: ed.status !== "" ? ed.status : "自动保存"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                }

                Rectangle {
                    width: 48
                    height: 3
                    radius: 1.5
                    color: CairnTheme.accent
                    opacity: 0.8
                }

                TextEdit {
                    id: body
                    width: parent.width
                    height: Math.max(contentHeight, 80)
                    text: backend.currentText
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    onTextChanged: {
                        if (!ed.loading) {
                            backend.queueSave(text);
                            ed.status = "编辑中…";
                        }
                    }
                }
            }
        }

        Shortcut {
            sequence: "Ctrl+S"
            onActivated: {
                backend.flush();
                ed.status = "已保存";
            }
        }
    }

    component EmptyState: Item {
        Column {
            anchors.centerIn: parent
            spacing: CairnTheme.spaceMd
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "\uE8A5"
                font.family: CairnTheme.iconFont
                font.pixelSize: 40
                color: CairnTheme.faint
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                text: "选择左侧笔记，或点 ＋ 新建"
                color: CairnTheme.muted
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
            }
        }
    }
}
