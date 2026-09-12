// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 右侧上下文信息面板：随领域（笔记 / 项目 / 社区）切换内容。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: dock
    color: CairnTheme.surface
    property string mode: "notes"

    Rectangle {
        anchors.left: parent.left
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
                    text: dock.mode === "community" ? "社区" : (dock.mode === "projects" ? "仓库" : "属性")
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                Text {
                    text: "\uE76C"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 12
                    color: CairnTheme.faint
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
                    }
                }

                // ===== 笔记：属性 =====
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 0
                    visible: dock.mode === "notes"
                    Section {
                        text: "基本"
                    }
                    PropRow {
                        k: "类型"
                        v: "笔记"
                    }
                    PropRow {
                        k: "空间"
                        v: "个人空间"
                    }
                    PropRow {
                        k: "可见性"
                        v: "私密"
                    }
                    Section {
                        text: "时间"
                    }
                    PropRow {
                        k: "创建"
                        v: "2026-09-10"
                    }
                    PropRow {
                        k: "修改"
                        v: "09:12"
                    }
                    Section {
                        text: "来源"
                    }
                    PropRow {
                        k: "派生自"
                        v: "石堆设计笔记"
                    }
                    Section {
                        text: "标签"
                    }
                    Flow {
                        Layout.leftMargin: CairnTheme.spaceMd
                        Layout.rightMargin: CairnTheme.spaceMd
                        Layout.bottomMargin: CairnTheme.spaceMd
                        Layout.fillWidth: true
                        spacing: 6
                        Repeater {
                            model: ["存储", "设计", "客户端"]
                            delegate: Rectangle {
                                width: tagText.implicitWidth + 16
                                height: 20
                                radius: 10
                                color: CairnTheme.elevated
                                border.color: CairnTheme.border
                                border.width: 1
                                Text {
                                    id: tagText
                                    anchors.centerIn: parent
                                    text: modelData
                                    color: CairnTheme.muted
                                    font.family: CairnTheme.fontFamily
                                    font.pixelSize: CairnTheme.fsTiny
                                }
                            }
                        }
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
                                color: CairnTheme.elevated
                                border.color: CairnTheme.border
                                border.width: 1
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
