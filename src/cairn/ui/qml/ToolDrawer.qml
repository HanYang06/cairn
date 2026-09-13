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
            "label": "族谱"
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

    // 顶部触发条
    Rectangle {
        id: trigger
        anchors.left: parent.left
        anchors.right: parent.right
        y: 0
        height: 10
        color: "transparent"

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            y: 2
            width: 148
            height: 5
            radius: 2.5
            color: CairnTheme.accent
            opacity: triggerHover.hovered || drawer.open ? 0.9 : 0.4
            Behavior on opacity {
                NumberAnimation {
                    duration: CairnTheme.durFast
                }
            }
        }
        HoverHandler {
            id: triggerHover
            onHoveredChanged: {
                if (hovered) {
                    closeTimer.stop();
                    drawer.open = true;
                } else if (!panelHover.hovered) {
                    closeTimer.restart();
                }
            }
        }
        TapHandler {
            onTapped: drawer.open = !drawer.open
        }
    }

    Timer {
        id: closeTimer
        interval: 300
        onTriggered: drawer.open = false
    }

    // 向下滑出的覆盖面板
    Rectangle {
        id: panel
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(parent.width - 24, 880)
        height: Math.min(parent.height - 12, 328)
        y: drawer.open ? 10 : -height - 12
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
                else if (!triggerHover.hovered)
                    closeTimer.restart();
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
                border.color: CairnTheme.border
                border.width: 1
                Text {
                    x: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    text: "\uE70F"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 13
                    color: CairnTheme.accent
                }
                Text {
                    x: 32
                    anchors.verticalCenter: parent.verticalCenter
                    text: "快速记录…"
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                }
            }

            GridLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
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
                        border.color: tileHover.hovered ? CairnTheme.accent : "transparent"
                        border.width: 1
                        Behavior on color {
                            ColorAnimation {
                                duration: CairnTheme.durFast
                            }
                        }

                        Column {
                            anchors.centerIn: parent
                            spacing: 7
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.glyph
                                font.family: CairnTheme.iconFont
                                font.pixelSize: 20
                                color: tileHover.hovered ? CairnTheme.accent : CairnTheme.muted
                            }
                            Text {
                                anchors.horizontalCenter: parent.horizontalCenter
                                text: modelData.label
                                color: CairnTheme.muted
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

            Text {
                Layout.fillWidth: true
                text: "单击＝开标签页 · 双击/右键＝临时显示在右侧"
                color: CairnTheme.faint
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
        }
    }
}
