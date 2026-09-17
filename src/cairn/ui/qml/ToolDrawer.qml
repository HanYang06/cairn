// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 工具册：从顶部向下滑出的覆盖式面板（开始菜单）。
// 领域与工具一体化，同一片小程序网格。
// 一切皆可拖拽：拖到左＝常驻、拖到中＝配置/操作、拖到右＝换展示。
import QtQuick
import QtQuick.Layouts
import "theme"

Item {
    id: drawer
    clip: true
    property bool open: false
    property bool editing: false
    // 搜索命令面板的结果（输入框有内容时展示）
    property var results: []
    // 鼠标离开后自动回收延迟（毫秒）：太短会误收，太长拖沓。
    property int autoCloseMs: 1500

    // 统一用「指针是否在触发条/面板内」判定，避免子项抢 hover 导致误收。
    HoverHandler {
        id: rootHover
        onPointChanged: drawer.syncHover()
    }

    // 关闭时清理搜索态，避免笔记列表停在过滤结果上。
    onOpenChanged: {
        if (!open) {
            capture.text = "";
            results = [];
            backend.filterNotes("");
        }
    }

    function syncHover() {
        if (!drawer.open) {
            closeTimer.stop();
            const t = rootHover.point.position;
            if (t.x >= trigger.x && t.x <= trigger.x + trigger.width && t.y >= trigger.y && t.y <= trigger.y + trigger.height)
                drawer.open = true;
            return;
        }
        const p = rootHover.point.position;
        const inTrigger = p.x >= trigger.x && p.x <= trigger.x + trigger.width && p.y >= trigger.y && p.y <= trigger.y + trigger.height;
        const inPanel = p.x >= panel.x && p.x <= panel.x + panel.width && p.y >= panel.y && p.y <= panel.y + panel.height;
        if (inTrigger || inPanel)
            closeTimer.stop();
        else
            closeTimer.restart();
    }
    signal launch(string id)
    signal preview(string id, string label)
    signal addRequested()

    property var apps: [
        {
            "id": "notes",
            "glyph": "\uE8A5",
            "label": "笔记"
        },
        {
            "id": "projects",
            "glyph": "\uE8B7",
            "label": "项目"
        },
        {
            "id": "community",
            "glyph": "\uE716",
            "label": "社区"
        },
        {
            "id": "graph",
            "glyph": "\uE8F1",
            "label": "图谱"
        },
        {
            "id": "outline",
            "glyph": "\uE8FD",
            "label": "大纲"
        },
        {
            "id": "relations",
            "glyph": "\uE71B",
            "label": "关系"
        },
        {
            "id": "lineage",
            "glyph": "\uE9D5",
            "label": "衍生"
        },
        {
            "id": "ai",
            "glyph": "\uE99A",
            "label": "AI 助手"
        },
        {
            "id": "history",
            "glyph": "\uE81C",
            "label": "版本"
        },
        {
            "id": "export",
            "glyph": "\uEDE1",
            "label": "导出"
        },
        {
            "id": "search",
            "glyph": "\uE721",
            "label": "搜索"
        },
        {
            "id": "tags",
            "glyph": "\uE8EC",
            "label": "标签"
        },
        {
            "id": "assets",
            "glyph": "\uE91B",
            "label": "资产"
        },
        {
            "id": "stats",
            "glyph": "\uE9D9",
            "label": "统计"
        }
    ]

    // 顶部触发条：放进标题栏内（居中一窄条），不与标签页重合。
    // 用 MouseArea（独占按下）压在标题栏拖拽区之上，避免与拖窗抢事件。
    MouseArea {
        id: trigger
        objectName: "drawerTrigger"
        anchors.horizontalCenter: parent.horizontalCenter
        y: 0
        width: 260
        height: 16
        z: 10
        onClicked: drawer.open = !drawer.open

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 9
            width: 148
            height: 4
            radius: 2
            color: CairnTheme.accent
            opacity: trigger.containsMouse || drawer.open ? 0.95 : 0.45
            Behavior on opacity {
                NumberAnimation {
                    duration: CairnTheme.durBase
                    easing.type: Easing.OutQuad
                }
            }
        }
    }

    Timer {
        id: closeTimer
        interval: drawer.autoCloseMs
        onTriggered: drawer.open = false
    }

    // 打开时，点面板外任意处立即回收；点面板内（含空白）不回收。
    MouseArea {
        id: backdrop
        anchors.fill: parent
        z: 1
        visible: drawer.open
        onClicked: function (mouse) {
            const insidePanel = mouse.x >= panel.x && mouse.x <= panel.x + panel.width
                && mouse.y >= panel.y && mouse.y <= panel.y + panel.height;
            if (!insidePanel)
                drawer.open = false;
        }
    }

    // 向下滑出的覆盖面板
    Rectangle {
        id: panel
        z: 5
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - 24, 880)
        height: Math.min(parent.height - 12, 328)
        y: drawer.open ? (CairnTheme.titleBarH + 8) : -(CairnTheme.titleBarH + height + 20)
        radius: CairnTheme.radiusXl
        color: CairnTheme.surface
        border.color: CairnTheme.border
        border.width: 1
        Behavior on y {
            NumberAnimation {
                duration: CairnTheme.durSlow
                easing.type: Easing.OutCubic
            }
        }

        HoverHandler {
            id: panelHover
            onHoveredChanged: {
                if (hovered)
                    closeTimer.stop();
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: CairnTheme.spaceXl
            spacing: CairnTheme.spaceLg

            RowLayout {
                Layout.fillWidth: true
                spacing: CairnTheme.spaceSm
                Text {
                    text: "工具册"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsLarge
                    font.weight: Font.DemiBold
                }
                Item {
                    Layout.fillWidth: true
                }
                Rectangle {
                    Layout.alignment: Qt.AlignVCenter
                    width: orgLabel.implicitWidth + 18
                    height: 26
                    radius: 13
                    color: orgHover.hovered ? CairnTheme.hover : "transparent"
                    Text {
                        id: orgLabel
                        anchors.centerIn: parent
                        text: "整理"
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    HoverHandler {
                        id: orgHover
                    }
                    TapHandler {
                        onTapped: drawer.editing = !drawer.editing
                    }
                }
                Rectangle {
                    Layout.alignment: Qt.AlignVCenter
                    width: addLabel.implicitWidth + 20
                    height: 26
                    radius: 13
                    color: addHover.hovered ? CairnTheme.selection : CairnTheme.bg
                    border.color: CairnTheme.accent
                    border.width: 1
                    Text {
                        id: addLabel
                        anchors.centerIn: parent
                        text: "＋ 添加"
                        color: CairnTheme.accent
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        font.weight: Font.Medium
                    }
                    HoverHandler {
                        id: addHover
                    }
                    TapHandler {
                        onTapped: drawer.addRequested()
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 36
                radius: CairnTheme.radiusSm
                color: CairnTheme.bg
                border.color: capture.activeFocus ? CairnTheme.accent : CairnTheme.border
                border.width: 1
                Text {
                    x: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    text: "\uE70F"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 13
                    color: CairnTheme.accent
                }
                TextInput {
                    id: capture
                    x: 32
                    width: parent.width - 44
                    anchors.verticalCenter: parent.verticalCenter
                    clip: true
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    selectByMouse: true
                    onTextChanged: drawer.results = backend.searchNotes(text)
                    onAccepted: {
                        const query = text.trim();
                        if (query === "")
                            return;
                        if (drawer.results.length > 0)
                            backend.openNote(drawer.results[0].oid);
                        else
                            backend.captureNote(query);
                        text = "";
                        drawer.results = [];
                    }
                    Keys.onEscapePressed: {
                        capture.text = "";
                        drawer.results = [];
                        backend.filterNotes("");
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        visible: capture.text === ""
                        text: "搜索笔记 / 命令，回车打开；无结果则新建…"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                    }
                }
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: capture.text === ""
                columns: 7
                columnSpacing: CairnTheme.spaceSm
                rowSpacing: CairnTheme.spaceSm

                Repeater {
                    model: drawer.apps
                    delegate: Rectangle {
                        id: tile
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        radius: CairnTheme.radius
                        color: tileHover.hovered ? CairnTheme.hover : "transparent"

                        Column {
                            anchors.centerIn: parent
                            spacing: 7
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.glyph
                                font.family: CairnTheme.iconFont
                                font.pixelSize: 20
                                color: tileHover.hovered ? CairnTheme.text : CairnTheme.muted
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.label
                                color: tileHover.hovered ? CairnTheme.text : CairnTheme.muted
                                font.family: CairnTheme.fontFamily
                                font.pixelSize: CairnTheme.fsTiny
                            }
                        }
                        Rectangle {
                            visible: drawer.editing
                            anchors.right: parent.right
                            anchors.top: parent.top
                            anchors.margins: 5
                            width: 16
                            height: 16
                            radius: 8
                            color: CairnTheme.bg
                            border.color: CairnTheme.border
                            border.width: 1
                            Text {
                                anchors.centerIn: parent
                                text: "\uE8BB"
                                font.family: CairnTheme.iconFont
                                font.pixelSize: 8
                                color: CairnTheme.muted
                            }
                        }
                        HoverHandler {
                            id: tileHover
                        }
                        TapHandler {
                            onTapped: drawer.launch(modelData.id)
                            onDoubleTapped: drawer.preview(modelData.id, modelData.label)
                        }
                        TapHandler {
                            acceptedButtons: Qt.RightButton
                            onTapped: drawer.preview(modelData.id, modelData.label)
                        }
                    }
                }
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: capture.text !== ""
                clip: true
                model: drawer.results
                spacing: 2
                boundsBehavior: Flickable.StopAtBounds

                delegate: Rectangle {
                    id: resultRow
                    width: ListView.view.width
                    height: 44
                    radius: CairnTheme.radiusSm
                    color: resMa.containsMouse ? CairnTheme.hover : "transparent"

                    Column {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.leftMargin: CairnTheme.spaceSm
                        anchors.rightMargin: CairnTheme.spaceSm
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2
                        Text {
                            width: parent.width
                            text: modelData.title
                            color: CairnTheme.text
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsSmall
                            elide: Text.ElideRight
                        }
                        Text {
                            width: parent.width
                            text: modelData.preview !== "" ? modelData.preview : "空笔记"
                            color: CairnTheme.faint
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                            elide: Text.ElideRight
                        }
                    }
                    MouseArea {
                        id: resMa
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            backend.openNote(modelData.oid);
                            capture.text = "";
                            drawer.results = [];
                            drawer.open = false;
                        }
                    }
                }
            }

            Text {
                Layout.fillWidth: true
                visible: text !== ""
                text: capture.text === "" ? "单击＝开标签页 · 双击/右键＝临时显示在右侧" : (drawer.results.length === 0 ? "无匹配：回车以该文本新建笔记 · Esc 清空" : "")
                color: CairnTheme.faint
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
        }
    }
}
