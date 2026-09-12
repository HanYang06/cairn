// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: side
    color: CairnTheme.surface

    property int selected: 0
    property var items: [
        {
            "title": "存储层的分块策略",
            "snippet": "FastCDC 16/64/256KiB，BLAKE3 派生 CID，去重以块为粒度。",
            "time": "09:12",
            "kind": "笔记"
        },
        {
            "title": "标签过滤与增量索引",
            "snippet": "iter 支持标签过滤；rebuild_index 走全量，日常只动增量。",
            "time": "昨天",
            "kind": "笔记"
        },
        {
            "title": "cairn-icon.svg",
            "snippet": "来自 VTracer 的矢量 logo，待补深浅两版。",
            "time": "昨天",
            "kind": "资产"
        },
        {
            "title": "项目：Cairn 客户端",
            "snippet": "本地优先知识工作台，网络层暂缓，先打通本地闭环。",
            "time": "周一",
            "kind": "项目"
        },
        {
            "title": "族谱：设计稿 v1",
            "snippet": "由「石堆设计笔记」派生，记录布局取舍与理由。",
            "time": "周一",
            "kind": "谱系"
        },
        {
            "title": "MCP 作为 AI 接入面",
            "snippet": "AI 只是工具调用者，不持有数据，通过 MCP 暴露能力。",
            "time": "上周",
            "kind": "灵感"
        }
    ]

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: CairnTheme.border
        opacity: 0.6
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
                    text: "收件箱"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                IconGlyph {
                    glyph: "\uE710"
                }
                IconGlyph {
                    glyph: "\uE712"
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: CairnTheme.spaceMd
            Layout.rightMargin: CairnTheme.spaceMd
            Layout.preferredHeight: 30
            radius: CairnTheme.radiusSm
            color: CairnTheme.bg
            border.color: CairnTheme.border
            border.width: 1
            Text {
                x: 9
                anchors.verticalCenter: parent.verticalCenter
                text: "\uE721"
                font.family: CairnTheme.iconFont
                font.pixelSize: 12
                color: CairnTheme.faint
            }
            Text {
                x: 28
                anchors.verticalCenter: parent.verticalCenter
                text: "筛选收件箱"
                color: CairnTheme.faint
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
            }
        }

        Item {
            Layout.preferredHeight: CairnTheme.spaceMd
        }

        Text {
            Layout.leftMargin: CairnTheme.spaceMd
            text: "今天"
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.weight: Font.DemiBold
            font.letterSpacing: 0.6
        }

        ListView {
            id: list
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            model: side.items
            boundsBehavior: Flickable.StopAtBounds

            delegate: Item {
                id: del
                width: list.width
                height: 64
                readonly property bool active: index === side.selected

                Rectangle {
                    anchors.fill: parent
                    color: del.active ? CairnTheme.selection : (delMa.containsMouse ? CairnTheme.hover : "transparent")
                    Behavior on color {
                        ColorAnimation {
                            duration: CairnTheme.durFast
                        }
                    }
                }
                Rectangle {
                    width: 2
                    height: parent.height
                    color: CairnTheme.accent
                    opacity: del.active ? 1 : 0
                    Behavior on opacity {
                        NumberAnimation {
                            duration: CairnTheme.durFast
                        }
                    }
                }
                Column {
                    anchors.fill: parent
                    anchors.leftMargin: CairnTheme.spaceMd
                    anchors.rightMargin: CairnTheme.spaceMd
                    anchors.topMargin: CairnTheme.spaceSm
                    anchors.bottomMargin: CairnTheme.spaceSm
                    spacing: 3
                    RowLayout {
                        width: parent.width
                        Text {
                            text: modelData.title
                            color: CairnTheme.text
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsSmall
                            font.weight: Font.Medium
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: modelData.time
                            color: CairnTheme.faint
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                        }
                    }
                    Text {
                        width: parent.width
                        text: modelData.snippet
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        maximumLineCount: 2
                        wrapMode: Text.WordWrap
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    id: delMa
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: side.selected = index
                }
            }
        }
    }

    component IconGlyph: Item {
        id: ig
        property string glyph
        Layout.preferredWidth: 26
        Layout.preferredHeight: 26
        Rectangle {
            anchors.fill: parent
            radius: CairnTheme.radiusSm
            color: igMa.containsMouse ? CairnTheme.hover : "transparent"
            Behavior on color {
                ColorAnimation {
                    duration: CairnTheme.durFast
                }
            }
        }
        Text {
            anchors.centerIn: parent
            text: ig.glyph
            font.family: CairnTheme.iconFont
            font.pixelSize: 13
            color: igMa.containsMouse ? CairnTheme.text : CairnTheme.muted
        }
        MouseArea {
            id: igMa
            anchors.fill: parent
            hoverEnabled: true
        }
    }
}
