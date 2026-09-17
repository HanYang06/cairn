// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 笔记格式工具栏：两行（字级 / 段级），按后端 toolLayout 渲染；溢出时可向下抽屉展开全部。
// 位置不写死，布局由 backend.toolLayout 驱动（将来可用户自定义）。
import QtQuick
import "theme"

Rectangle {
    id: bar
    property string activeLineId: ""
    property bool toolsEnabled: false
    signal toolTriggered(string tid)

    readonly property int btn: 26
    readonly property int sep: 7
    readonly property real avail: width - 30

    property var metaById: ({})
    property bool drawerOpen: false

    implicitHeight: toolsEnabled ? (rowsCol.implicitHeight + 8) : 0
    visible: toolsEnabled
    color: CairnTheme.surface

    function rebuildMeta() {
        var map = ({});
        var list = backend.tools;
        for (var i = 0; i < list.length; ++i)
            map[list[i].id] = list[i];
        bar.metaById = map;
    }

    function rowWidth(row) {
        var total = 0;
        for (var g = 0; g < row.length; ++g) {
            total += row[g].length * bar.btn;
            if (g > 0)
                total += bar.sep;
        }
        return total;
    }

    readonly property bool anyOverflow: {
        var rows = backend.toolLayout;
        for (var i = 0; i < rows.length; ++i) {
            if (bar.rowWidth(rows[i]) > bar.avail)
                return true;
        }
        return false;
    }

    Component.onCompleted: rebuildMeta()

    Connections {
        target: backend
        function onCurrentChanged() {
            bar.rebuildMeta();
        }
    }

    Column {
        id: rowsCol
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: 4
        anchors.rightMargin: 30
        spacing: 2

        Repeater {
            model: backend.toolLayout
            delegate: Flickable {
                id: rowFlick
                width: rowsCol.width
                height: 28
                clip: true
                contentWidth: rowItem.implicitWidth
                contentHeight: height
                interactive: false
                boundsBehavior: Flickable.StopAtBounds

                Row {
                    id: rowItem
                    height: parent.height
                    Repeater {
                        model: modelData
                        delegate: Row {
                            height: rowItem.height
                            spacing: 1
                            Repeater {
                                model: modelData
                                delegate: ToolBtn {
                                    tid: modelData
                                    meta: bar.metaById[modelData] || ({})
                                    onClicked: bar.toolTriggered(modelData)
                                }
                            }
                            Rectangle {
                                width: 1
                                height: 16
                                anchors.verticalCenter: parent.verticalCenter
                                color: CairnTheme.border
                                opacity: 0.6
                            }
                        }
                    }
                }
            }
        }
    }

    // 溢出/展开箭头
    Rectangle {
        id: moreBtn
        anchors.right: parent.right
        anchors.rightMargin: 4
        anchors.top: parent.top
        anchors.topMargin: 6
        width: 22
        height: 22
        radius: CairnTheme.radiusSm
        color: (moreMa.containsMouse || bar.drawerOpen) ? CairnTheme.hover : "transparent"
        Text {
            anchors.centerIn: parent
            text: "\uE76C"
            font.family: CairnTheme.iconFont
            font.pixelSize: 10
            color: (bar.anyOverflow || bar.drawerOpen) ? CairnTheme.accent : CairnTheme.faint
        }
        HoverHandler {
            onHoveredChanged: hovered ? Tips.show("更多工具", moreBtn) : Tips.hide()
        }
        MouseArea {
            id: moreMa
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: bar.drawerOpen = !bar.drawerOpen
        }
    }

    // 向下抽屉：展开全部工具（溢出时用）
    Rectangle {
        id: drawer
        visible: bar.drawerOpen
        anchors.top: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        height: flow.implicitHeight + 16
        color: CairnTheme.elevated
        border.color: CairnTheme.border
        border.width: 1
        z: 60

        Flow {
            id: flow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.margins: 8
            spacing: 2
            Repeater {
                model: backend.tools
                delegate: ToolBtn {
                    tid: modelData.id
                    meta: modelData
                    onClicked: bar.toolTriggered(modelData.id)
                }
            }
        }
    }

    component ToolBtn: Rectangle {
        id: button
        property string tid: ""
        property var meta: ({})
        signal clicked()
        width: 26
        height: 24
        radius: CairnTheme.radiusSm
        color: bMa.containsMouse ? CairnTheme.hover : "transparent"

        Text {
            anchors.centerIn: parent
            visible: (button.meta.text || "") === ""
            text: button.meta.glyph || ""
            font.family: CairnTheme.iconFont
            font.pixelSize: 12
            color: CairnTheme.muted
        }
        Text {
            anchors.centerIn: parent
            visible: (button.meta.text || "") !== ""
            text: button.meta.text || ""
            color: CairnTheme.text
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.weight: button.meta.id === "bold" ? Font.Bold : Font.Normal
            font.italic: button.meta.id === "italic"
            font.underline: button.meta.id === "underline"
            font.strikeout: button.meta.id === "strike"
        }
        HoverHandler {
            onHoveredChanged: hovered ? Tips.show(button.meta.label || "", button) : Tips.hide()
        }
        MouseArea {
            id: bMa
            anchors.fill: parent
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: button.clicked()
        }
    }
}
