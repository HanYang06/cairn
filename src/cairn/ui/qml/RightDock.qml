// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 右侧上下文信息面板：KV 属性检查器 + 关系文字树；随领域（笔记 / 项目 / 社区）切换。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: dock
    color: CairnTheme.surface
    property string mode: "notes"
    property string preview: ""
    signal collapseRequested()

    Rectangle {
        anchors.left: parent.left
        width: 1
        height: parent.height
        color: CairnTheme.borderFaint
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: dock.preview !== "" ? ("临时显示 · " + dock.preview) : (dock.mode === "community" ? "社区" : (dock.mode === "projects" ? "仓库" : "属性"))
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                Text {
                    id: collapseGlyph
                    text: "\uE76C"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 12
                    color: collapseMa.containsMouse ? CairnTheme.text : CairnTheme.faint
                    HoverHandler {
                        onHoveredChanged: hovered ? Tips.show("收起属性", collapseGlyph) : Tips.hide()
                    }
                    MouseArea {
                        id: collapseMa
                        anchors.fill: parent
                        anchors.margins: -6
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: dock.collapseRequested()
                    }
                }
            }
        }

        Flickable {
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            contentHeight: body.implicitHeight

            ColumnLayout {
                id: body
                width: parent.width
                spacing: 0

                component Section: Text {
                    Layout.leftMargin: CairnTheme.spaceMd
                    Layout.topMargin: CairnTheme.spaceMd
                    Layout.bottomMargin: CairnTheme.spaceXs
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    font.weight: Font.DemiBold
                    font.letterSpacing: 0.6
                }

                component PropRow: Item {
                    id: r
                    property string k: ""
                    property string v: ""
                    Layout.leftMargin: CairnTheme.spaceMd
                    Layout.rightMargin: CairnTheme.spaceMd
                    Layout.preferredHeight: 26
                    Layout.fillWidth: true
                    Text {
                        anchors.left: parent.left
                        anchors.verticalCenter: parent.verticalCenter
                        text: r.k
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    Text {
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        text: r.v
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        elide: Text.ElideRight
                        width: parent.width * 0.6
                        horizontalAlignment: Text.AlignRight
                    }
                }

                // ===== 笔记：KV 属性检查器 =====
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    visible: dock.mode === "notes" && dock.preview === "" && backend.currentOid !== ""

                    Section {
                        text: "属性"
                    }

                    Column {
                        Layout.fillWidth: true
                        spacing: 2

                        Repeater {
                            model: backend.currentProperties
                            delegate: Item {
                                id: entry
                                width: parent.width
                                height: content.implicitHeight

                                Column {
                                    id: content
                                    width: parent.width
                                    spacing: 6

                                    Item {
                                        width: parent.width
                                        height: 28
                                        implicitHeight: 28
                                        Text {
                                            anchors.left: parent.left
                                            anchors.leftMargin: CairnTheme.spaceMd
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.key
                                            color: CairnTheme.muted
                                            font.family: CairnTheme.fontFamily
                                            font.pixelSize: CairnTheme.fsTiny
                                        }

                                        // 只读文本：浅；可编辑：深
                                        Text {
                                            visible: modelData.type === "text" || modelData.type === "count"
                                            anchors.right: parent.right
                                            anchors.rightMargin: CairnTheme.spaceMd
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: parent.width * 0.62
                                            text: "" + modelData.value
                                            color: modelData.editable ? CairnTheme.text : CairnTheme.faint
                                            font.family: CairnTheme.fontFamily
                                            font.pixelSize: CairnTheme.fsTiny
                                            elide: Text.ElideRight
                                            horizontalAlignment: Text.AlignRight
                                        }

                                        Text {
                                            visible: modelData.type === "tags"
                                            anchors.right: parent.right
                                            anchors.rightMargin: CairnTheme.spaceMd
                                            anchors.verticalCenter: parent.verticalCenter
                                            text: modelData.value.length + " 个"
                                            color: CairnTheme.text
                                            font.family: CairnTheme.fontFamily
                                            font.pixelSize: CairnTheme.fsTiny
                                        }

                                        // 布尔：可编辑开关
                                        Rectangle {
                                            visible: modelData.type === "bool"
                                            anchors.right: parent.right
                                            anchors.rightMargin: CairnTheme.spaceMd
                                            anchors.verticalCenter: parent.verticalCenter
                                            width: 34
                                            height: 18
                                            radius: 9
                                            color: modelData.value ? CairnTheme.accent : CairnTheme.borderFaint
                                            Behavior on color {
                                                ColorAnimation {
                                                    duration: CairnTheme.durBase
                                                    easing.type: Easing.InOutQuad
                                                }
                                            }
                                            Rectangle {
                                                width: 14
                                                height: 14
                                                radius: 7
                                                y: 2
                                                x: modelData.value ? 18 : 2
                                                color: "#FFFFFF"
                                                Behavior on x {
                                                    NumberAnimation {
                                                        duration: CairnTheme.durBase
                                                        easing.type: Easing.InOutQuad
                                                    }
                                                }
                                            }
                                            MouseArea {
                                                anchors.fill: parent
                                                hoverEnabled: true
                                                cursorShape: Qt.PointingHandCursor
                                                onClicked: {
                                                    if (modelData.id === "favorite")
                                                        backend.toggleFavorite(backend.currentOid);
                                                    else if (modelData.id === "archived")
                                                        backend.toggleArchive(backend.currentOid);
                                                }
                                            }
                                        }
                                    }

                                    // 标签：KV 编辑（云控制台风格）
                                    Item {
                                        visible: modelData.type === "tags"
                                        width: parent.width
                                        implicitHeight: tagCol.implicitHeight
                                        Column {
                                            id: tagCol
                                            x: CairnTheme.spaceMd
                                            width: parent.width - CairnTheme.spaceMd * 2
                                            spacing: 4

                                            Repeater {
                                                model: backend.tagPairs
                                                delegate: RowLayout {
                                                    width: parent.width
                                                    spacing: 6

                                                    Rectangle {
                                                        Layout.preferredWidth: 88
                                                        implicitWidth: 88
                                                        implicitHeight: 24
                                                        radius: CairnTheme.radiusSm
                                                        color: tagKey.activeFocus ? CairnTheme.bg : CairnTheme.hover
                                                        border.color: tagKey.activeFocus ? CairnTheme.accent : "transparent"
                                                        border.width: 1
                                                        TextInput {
                                                            id: tagKey
                                                            anchors.fill: parent
                                                            anchors.leftMargin: 8
                                                            anchors.rightMargin: 8
                                                            verticalAlignment: TextInput.AlignVCenter
                                                            clip: true
                                                            text: modelData.key
                                                            color: CairnTheme.text
                                                            font.family: CairnTheme.fontFamily
                                                            font.pixelSize: CairnTheme.fsTiny
                                                            selectByMouse: true
                                                            onEditingFinished: backend.replaceTag(modelData.raw, tagKey.text, tagValue.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: ":"
                                                        color: CairnTheme.faint
                                                        font.family: CairnTheme.fontFamily
                                                        font.pixelSize: CairnTheme.fsTiny
                                                    }
                                                    Rectangle {
                                                        Layout.fillWidth: true
                                                        implicitHeight: 24
                                                        radius: CairnTheme.radiusSm
                                                        color: tagValue.activeFocus ? CairnTheme.bg : CairnTheme.hover
                                                        border.color: tagValue.activeFocus ? CairnTheme.accent : "transparent"
                                                        border.width: 1
                                                        TextInput {
                                                            id: tagValue
                                                            anchors.fill: parent
                                                            anchors.leftMargin: 8
                                                            anchors.rightMargin: 8
                                                            verticalAlignment: TextInput.AlignVCenter
                                                            clip: true
                                                            text: modelData.value
                                                            color: CairnTheme.muted
                                                            font.family: CairnTheme.fontFamily
                                                            font.pixelSize: CairnTheme.fsTiny
                                                            selectByMouse: true
                                                            onEditingFinished: backend.replaceTag(modelData.raw, tagKey.text, tagValue.text)
                                                        }
                                                    }
                                                    Text {
                                                        text: "\uE8BB"
                                                        font.family: CairnTheme.iconFont
                                                        font.pixelSize: 9
                                                        color: tagRemove.containsMouse ? CairnTheme.danger : CairnTheme.faint
                                                        MouseArea {
                                                            id: tagRemove
                                                            anchors.fill: parent
                                                            anchors.margins: -6
                                                            hoverEnabled: true
                                                            cursorShape: Qt.PointingHandCursor
                                                            onClicked: backend.removeTag(modelData.raw)
                                                        }
                                                    }
                                                }
                                            }

                                            Rectangle {
                                                width: parent.width
                                                implicitHeight: 24
                                                radius: CairnTheme.radiusSm
                                                color: kvTagInput.activeFocus ? CairnTheme.bg : CairnTheme.hover
                                                border.color: kvTagInput.activeFocus ? CairnTheme.accent : "transparent"
                                                border.width: 1
                                                TextInput {
                                                    id: kvTagInput
                                                    anchors.fill: parent
                                                    anchors.leftMargin: 8
                                                    anchors.rightMargin: 8
                                                    verticalAlignment: TextInput.AlignVCenter
                                                    clip: true
                                                    color: CairnTheme.text
                                                    font.family: CairnTheme.fontFamily
                                                    font.pixelSize: CairnTheme.fsTiny
                                                    selectByMouse: true
                                                    onAccepted: {
                                                        backend.addTag(kvTagInput.text);
                                                        kvTagInput.text = "";
                                                    }
                                                    Text {
                                                        anchors.verticalCenter: parent.verticalCenter
                                                        visible: kvTagInput.text === ""
                                                        text: "＋ 添加标签（K:V 或 K）"
                                                        color: CairnTheme.faint
                                                        font.family: CairnTheme.fontFamily
                                                        font.pixelSize: CairnTheme.fsTiny
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // ---- 关系：文字树（只读）----
                    Section {
                        text: "关系"
                    }
                    Text {
                        Layout.leftMargin: CairnTheme.spaceMd
                        Layout.bottomMargin: CairnTheme.spaceXs
                        visible: backend.currentAncestors.length === 0 && backend.currentDescendants.length === 0
                        text: "无"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    Repeater {
                        model: backend.currentAncestors
                        delegate: Rectangle {
                            id: ancRow
                            Layout.fillWidth: true
                            Layout.leftMargin: CairnTheme.spaceMd
                            Layout.rightMargin: CairnTheme.spaceMd
                            Layout.preferredHeight: 24
                            radius: CairnTheme.radiusSm
                            color: ancMa.containsMouse ? CairnTheme.hover : "transparent"
                            Text {
                                x: 8 + index * 12
                                anchors.right: parent.right
                                anchors.rightMargin: CairnTheme.spaceSm
                                anchors.verticalCenter: parent.verticalCenter
                                text: "\u2196 " + modelData.title
                                color: CairnTheme.muted
                                font.family: CairnTheme.fontFamily
                                font.pixelSize: CairnTheme.fsTiny
                                elide: Text.ElideRight
                            }
                            MouseArea {
                                id: ancMa
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: backend.openNote(modelData.oid)
                            }
                        }
                    }
                    Repeater {
                        model: backend.currentDescendants
                        delegate: Rectangle {
                            id: descRow
                            Layout.fillWidth: true
                            Layout.leftMargin: CairnTheme.spaceMd
                            Layout.rightMargin: CairnTheme.spaceMd
                            Layout.preferredHeight: 24
                            radius: CairnTheme.radiusSm
                            color: descMa.containsMouse ? CairnTheme.hover : "transparent"
                            Text {
                                x: 8 + index * 12
                                anchors.right: parent.right
                                anchors.rightMargin: CairnTheme.spaceSm
                                anchors.verticalCenter: parent.verticalCenter
                                text: "\u2198 " + modelData.title
                                color: CairnTheme.muted
                                font.family: CairnTheme.fontFamily
                                font.pixelSize: CairnTheme.fsTiny
                                elide: Text.ElideRight
                            }
                            MouseArea {
                                id: descMa
                                anchors.fill: parent
                                hoverEnabled: true
                                onClicked: backend.openNote(modelData.oid)
                            }
                        }
                    }
                    Item {
                        Layout.preferredHeight: CairnTheme.spaceMd
                    }
                }

                // ===== 项目：仓库信息 =====
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    visible: dock.mode === "projects"
                    Section {
                        text: "仓库"
                    }
                    PropRow {
                        k: "名称"
                        v: "Cairn 客户端"
                    }
                    PropRow {
                        k: "分支"
                        v: "main"
                    }
                    PropRow {
                        k: "版本"
                        v: "0.0.1"
                    }
                    PropRow {
                        k: "节点"
                        v: "24"
                    }
                    Section {
                        text: "活动"
                    }
                    PropRow {
                        k: "状态"
                        v: "活跃"
                    }
                    PropRow {
                        k: "最近提交"
                        v: "09:12"
                    }
                    Section {
                        text: "参与者"
                    }
                    Flow {
                        Layout.leftMargin: CairnTheme.spaceMd
                        Layout.rightMargin: CairnTheme.spaceMd
                        Layout.bottomMargin: CairnTheme.spaceMd
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: ["韩", "石", "AI"]
                            delegate: Rectangle {
                                width: 26
                                height: 26
                                radius: 13
                                color: CairnTheme.hover
                                Text {
                                    anchors.centerIn: parent
                                    text: modelData
                                    color: CairnTheme.accent
                                    font.family: CairnTheme.fontFamily
                                    font.pixelSize: CairnTheme.fsTiny
                                }
                            }
                        }
                    }
                }

                // ===== 社区：成员 / 角色 / 规则 / 治理 / AI =====
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    visible: dock.mode === "community"
                    Section {
                        text: "成员"
                    }
                    PropRow {
                        k: "总数"
                        v: "1,204"
                    }
                    PropRow {
                        k: "在线"
                        v: "37"
                    }
                    Section {
                        text: "角色"
                    }
                    PropRow {
                        k: "所有者"
                        v: "韩"
                    }
                    PropRow {
                        k: "管理员"
                        v: "3 位"
                    }
                    PropRow {
                        k: "成员"
                        v: "1,200 位"
                    }
                    Section {
                        text: "规则"
                    }
                    PropRow {
                        k: "置顶"
                        v: "社区公约 v2"
                    }
                    PropRow {
                        k: "待审"
                        v: "2 条"
                    }
                    Section {
                        text: "治理"
                    }
                    PropRow {
                        k: "进行中提案"
                        v: "1"
                    }
                    PropRow {
                        k: "投票截止"
                        v: "3 天"
                    }
                    Section {
                        text: "AI 关系"
                    }
                    PropRow {
                        k: "自动整理"
                        v: "开启"
                    }
                    PropRow {
                        k: "可读范围"
                        v: "仅公开区"
                    }
                    Item {
                        Layout.preferredHeight: CairnTheme.spaceMd
                    }
                }
            }
        }
    }
}
