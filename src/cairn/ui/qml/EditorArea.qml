// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: area
    color: CairnTheme.surface

    // 布局控制：由 Shell 注入，操作就放在内容旁边。
    property bool inspectorOpen: true
    property bool focusMode: false
    signal toggleInspector()
    signal shareRequested(real x, real y)

    // 正文可读宽度：聚焦时放宽，普通时保持舒适行长。
    readonly property int contentMaxWidth: focusMode ? 980 : 720

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

            RowLayout {
                anchors.fill: parent
                spacing: 0

                Row {
                    id: tabsRow
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true

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
            }
            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: CairnTheme.borderFaint
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

    // 命令带里的紧凑幽灵按钮：无边框，仅靠底色/字色表达悬停与激活。
    component CmdButton: Rectangle {
        id: cb
        property string glyph: ""
        property string label: ""
        property bool active: false
        property bool danger: false
        signal clicked()
        // 用 implicitWidth：布局（RowLayout）据此分配并在文案变化时重排，避免重叠。
        implicitWidth: cbText.implicitWidth + (cb.glyph !== "" ? 24 : 16)
        implicitHeight: 26
        radius: CairnTheme.radiusSm
        color: cb.active ? CairnTheme.selection : (cbMa.containsMouse ? CairnTheme.hover : "transparent")
        Behavior on color {
            ColorAnimation {
                duration: CairnTheme.durFast
            }
        }
        Row {
            anchors.centerIn: parent
            spacing: 4
            Text {
                visible: cb.glyph !== ""
                anchors.verticalCenter: parent.verticalCenter
                text: cb.glyph
                font.family: CairnTheme.iconFont
                font.pixelSize: 11
                color: cb.danger ? CairnTheme.danger : (cb.active ? CairnTheme.accent : CairnTheme.muted)
            }
            Text {
                id: cbText
                anchors.verticalCenter: parent.verticalCenter
                text: cb.label
                color: cb.danger ? CairnTheme.danger : (cb.active ? CairnTheme.text : CairnTheme.muted)
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
        }
        MouseArea {
            id: cbMa
            anchors.fill: parent
            hoverEnabled: true
            onClicked: cb.clicked()
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
                applyContent();
                contentFade.restart();
            }
            function onContentChanged() {
                ed.status = "已保存";
            }
        }

        function applyContent() {
            ed.loading = true;
            titleInput.text = backend.currentTitle;
            body.text = backend.currentText;
            ed.loading = false;
            ed.status = "";
        }

        // 极简：换文后一次短淡入，不做位移、不做淡出。
        NumberAnimation {
            id: contentFade
            target: col
            property: "opacity"
            from: 0
            to: 1
            duration: CairnTheme.durFast
            easing.type: Easing.OutQuad
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: 0

            // ===== 命令带：动作（标签编辑已移入属性面板）=====
            Rectangle {
                Layout.fillWidth: true
                color: CairnTheme.surface
                implicitHeight: band.implicitHeight

                ColumnLayout {
                    id: band
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    spacing: 0

                    // —— 动作行 ——
                    Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: 34
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: CairnTheme.spaceLg
                            anchors.rightMargin: CairnTheme.spaceSm
                            spacing: CairnTheme.spaceXs

                            CmdButton {
                                glyph: backend.currentFavorite ? "\uE735" : "\uE734"
                                label: backend.currentFavorite ? "已收藏" : "收藏"
                                active: backend.currentFavorite
                                onClicked: backend.toggleFavorite(backend.currentOid)
                            }
                            CmdButton {
                                glyph: "\uE7B8"
                                label: backend.currentArchived ? "已归档" : "归档"
                                active: backend.currentArchived
                                onClicked: backend.toggleArchive(backend.currentOid)
                            }
                            CmdButton {
                                glyph: "\uE8F1"
                                label: "复刻"
                                onClicked: backend.deriveNote()
                            }
                            CmdButton {
                                glyph: "\uE71B"
                                label: "关系"
                                onClicked: backend.openRelations()
                            }
                            CmdButton {
                                glyph: "\uE81C"
                                label: "历史"
                                onClicked: backend.openHistory(backend.currentOid)
                            }
                            CmdButton {
                                id: shareBtn
                                objectName: "bandShare"
                                glyph: "\uE72E"
                                label: backend.currentShares.length > 0 ? "已分享 " + backend.currentShares.length : "分享"
                                active: backend.currentShares.length > 0
                                onClicked: {
                                    const p = shareBtn.mapToItem(area, 0, shareBtn.height + 4);
                                    area.shareRequested(p.x, p.y);
                                }
                            }
                            Item {
                                Layout.fillWidth: true
                            }
                            CmdButton {
                                glyph: "\uE946"
                                label: "属性"
                                active: area.inspectorOpen && !area.focusMode
                                onClicked: area.toggleInspector()
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: CairnTheme.borderFaint
            }

            Flickable {
                id: flick
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentWidth: width
                contentHeight: col.height + 64
                clip: true

                Column {
                    id: col
                    width: Math.min(flick.width - 72, area.contentMaxWidth)
                    x: Math.max(36, (flick.width - width) / 2)
                    y: 36
                    spacing: CairnTheme.spaceLg

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
                        opacity: 0.5
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
        // 空白处双击＝新建空笔记。
        TapHandler {
            acceptedButtons: Qt.LeftButton
            onDoubleTapped: backend.createNote()
        }
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
                text: "双击空白处新建笔记，或选择左侧笔记"
                color: CairnTheme.muted
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
            }
        }
    }
}
