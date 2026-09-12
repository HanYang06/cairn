// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: area
    color: CairnTheme.surface

    // 标签页 = 正在处理的任务
    property var tabs: [
        {
            "title": "石堆设计笔记",
            "kind": "note"
        },
        {
            "title": "项目：Cairn 客户端",
            "kind": "project"
        },
        {
            "title": "QML 外壳草案",
            "kind": "note"
        }
    ]
    property int currentTab: 0

    function kindColor(kind) {
        if (kind === "project")
            return CairnTheme.accentAlt;
        if (kind === "graph")
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
                    model: area.tabs
                    delegate: Rectangle {
                        id: tab
                        width: Math.min(240, Math.max(130, tabText.implicitWidth + 70))
                        height: parent.height
                        color: index === area.currentTab ? CairnTheme.surface : (tabMa.containsMouse ? CairnTheme.hover : "transparent")
                        Behavior on color {
                            ColorAnimation {
                                duration: CairnTheme.durFast
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 2
                            color: CairnTheme.accent
                            opacity: index === area.currentTab ? 1 : 0
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
                            color: area.kindColor(modelData.kind)
                        }
                        Text {
                            id: tabText
                            anchors.left: parent.left
                            anchors.leftMargin: 26
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.title
                            color: index === area.currentTab ? CairnTheme.text : CairnTheme.muted
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsSmall
                        }
                        Text {
                            anchors.right: parent.right
                            anchors.rightMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            text: "\uE8BB"
                            visible: index === area.currentTab
                            font.family: CairnTheme.iconFont
                            font.pixelSize: 9
                            color: CairnTheme.faint
                        }
                        MouseArea {
                            id: tabMa
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: area.currentTab = index
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

        NoteView {
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    component NoteView: Item {
        Column {
            width: Math.min(parent.width - 72, 720)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 36
            spacing: CairnTheme.spaceMd

            Text {
                text: "石堆设计笔记"
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTitle
                font.weight: Font.DemiBold
            }
            Row {
                height: 22
                spacing: CairnTheme.spaceSm
                Rectangle {
                    width: metaNote.implicitWidth + 18
                    height: 22
                    radius: 11
                    color: CairnTheme.elevated
                    Text {
                        id: metaNote
                        anchors.centerIn: parent
                        text: "笔记"
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                }
                Rectangle {
                    width: metaVis.implicitWidth + 18
                    height: 22
                    radius: 11
                    color: CairnTheme.elevated
                    Text {
                        id: metaVis
                        anchors.centerIn: parent
                        text: "私密"
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                }
                Item {
                    width: metaTime.implicitWidth
                    height: 22
                    Text {
                        id: metaTime
                        anchors.verticalCenter: parent.verticalCenter
                        text: "09:12 更新"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                }
                Item {
                    width: relationshipLink.implicitWidth
                    height: 22
                    Text {
                        id: relationshipLink
                        anchors.verticalCenter: parent.verticalCenter
                        text: "在关系中打开 ›"
                        color: CairnTheme.accent
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                }
            }
            Rectangle {
                width: 48
                height: 3
                radius: 1.5
                color: CairnTheme.accent
                opacity: 0.8
            }
            Text {
                width: parent.width
                text: "内容先落在本地对象池，再进入索引；块级去重让相同内容只存一份。CID 由 BLAKE3 派生密钥计算，删除与 GC 走标记清除，默认保留最近 30 天的版本链。"
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsBody
                lineHeight: 1.55
                wrapMode: Text.WordWrap
            }
            Text {
                width: parent.width
                text: "把「收」和「编」分开：收集时零摩擦，整理时再建立关系与归属。关系不是常驻面板，而是一个随时可打开的特殊页面。"
                color: CairnTheme.muted
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsBody
                lineHeight: 1.55
                wrapMode: Text.WordWrap
            }
        }
    }
}
