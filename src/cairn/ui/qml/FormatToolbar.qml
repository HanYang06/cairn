// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 笔记格式工具栏：两行（编辑型），按后端 toolLayout 渲染；溢出/其余类别走向下抽屉。
// 位置不写死，布局由 backend.toolLayout 驱动（将来可用户自定义）。
// 按钮三态由 backend.toolState 提供：生效（高亮）/ 未生效 / 混合（淡底）。
import QtQuick
import QtQuick.Controls
import "theme"

Rectangle {
    id: bar
    property string activeLineId: ""
    property bool toolsEnabled: false
    signal toolTriggered(string tid, var source)

    readonly property int btn: 26
    readonly property int sep: 7
    readonly property real avail: width - 30

    property var metaById: ({})
    property var stateMap: ({})
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

    // 拉取当前行/选区的工具状态（只读，高亮用）。
    function refreshState(start, end) {
        if (!bar.activeLineId) {
            bar.stateMap = ({});
            return;
        }
        bar.stateMap = backend.toolState(bar.activeLineId, start || 0, end || 0);
    }

    function activeOf(tid) {
        return bar.stateMap[tid] === true;
    }

    function mixedOf(tid) {
        return bar.stateMap[tid] === null;
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

    Component.onCompleted: {
        rebuildMeta();
        refreshState();
        if (bar.drawerOpen)
            toolPopup.open();
    }

    onActiveLineIdChanged: refreshState()

    onDrawerOpenChanged: {
        if (bar.drawerOpen)
            toolPopup.open();
        else
            toolPopup.close();
    }

    Connections {
        target: backend
        function onCurrentChanged() {
            bar.rebuildMeta();
            bar.refreshState();
        }
        function onContentChanged() {
            bar.refreshState();
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
                                    id: rowBtn
                                    tid: modelData
                                    meta: bar.metaById[modelData] || ({})
                                    active: bar.activeOf(modelData)
                                    mixed: bar.mixedOf(modelData)
                                    onClicked: bar.toolTriggered(modelData, rowBtn)
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

    // 溢出抽屉：按类别分组的紧凑工具网格。
    // 用 Popup（窗口覆盖层）保证盖在最上层、不与正文糊在一起；点外部 / Esc 自动回收。
    Popup {
        id: toolPopup
        parent: bar
        x: 0
        y: bar.height
        width: bar.width
        padding: 0
        modal: false
        focus: true
        closePolicy: Popup.CloseOnPressOutside | Popup.CloseOnEscape
        onClosed: bar.drawerOpen = false

        enter: Transition {
            NumberAnimation {
                property: "opacity"
                from: 0
                to: 1
                duration: CairnTheme.durBase
                easing.type: Easing.OutQuad
            }
        }
        exit: Transition {
            NumberAnimation {
                property: "opacity"
                from: 1
                to: 0
                duration: CairnTheme.durFast
                easing.type: Easing.InQuad
            }
        }

        background: Rectangle {
            color: CairnTheme.surface
            border.color: CairnTheme.border
            border.width: 1
            radius: CairnTheme.radiusSm
            bottomLeftRadius: CairnTheme.radiusLg
            bottomRightRadius: CairnTheme.radiusLg
        }

        contentItem: Column {
            id: drawerCol
            padding: CairnTheme.spaceMd
            spacing: CairnTheme.spaceSm

            Repeater {
                model: backend.toolGroups
                delegate: Column {
                    width: drawerCol.width - drawerCol.padding * 2
                    spacing: 4
                    Text {
                        text: modelData.label
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    Grid {
                        width: parent.width
                        spacing: 2
                        columns: Math.max(4, Math.floor(width / 68))
                        Repeater {
                            model: modelData.tools
                            delegate: DrawerTile {
                                id: drawerTile
                                tid: modelData.id
                                meta: modelData
                                active: bar.activeOf(modelData.id)
                                mixed: bar.mixedOf(modelData.id)
                                onClicked: {
                                    toolPopup.close();
                                    bar.toolTriggered(modelData.id, drawerTile);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    component ToolBtn: Rectangle {
        id: button
        property string tid: ""
        property var meta: ({})
        property bool active: false
        property bool mixed: false
        readonly property bool unavailable: button.meta.available === false
        signal clicked()
        width: 26
        height: 24
        radius: CairnTheme.radiusSm
        opacity: button.unavailable ? 0.35 : 1
        color: {
            if (button.unavailable)
                return "transparent";
            if (button.active)
                return CairnTheme.selection;
            if (button.hovered || button.mixed)
                return CairnTheme.hover;
            return "transparent";
        }
        property alias hovered: bHover.hovered

        Text {
            anchors.centerIn: parent
            visible: (button.meta.text || "") === ""
            text: button.meta.glyph || ""
            font.family: CairnTheme.iconFont
            font.pixelSize: 12
            color: button.active ? CairnTheme.accent : CairnTheme.muted
        }
        Text {
            anchors.centerIn: parent
            visible: (button.meta.text || "") !== ""
            text: button.meta.text || ""
            color: button.active ? CairnTheme.accent : CairnTheme.text
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.weight: button.meta.id === "bold" ? Font.Bold : Font.Normal
            font.italic: button.meta.id === "italic"
            font.underline: button.meta.id === "underline"
            font.strikeout: button.meta.id === "strike"
        }
        HoverHandler {
            id: bHover
            onHoveredChanged: {
                if (!hovered)
                    Tips.hide();
                else if (button.unavailable)
                    Tips.show((button.meta.label || "") + "（预留）", button);
                else
                    Tips.show(button.meta.label || "", button);
            }
        }
        MouseArea {
            id: bMa
            anchors.fill: parent
            enabled: !button.unavailable
            hoverEnabled: true
            cursorShape: button.unavailable ? Qt.ArrowCursor : Qt.PointingHandCursor
            onClicked: button.clicked()
        }
    }

    // 抽屉里的工具格：图标 / 文本 + 标签，紧凑排布，便于速览与查找。
    component DrawerTile: Rectangle {
        id: tile
        property string tid: ""
        property var meta: ({})
        property bool active: false
        property bool mixed: false
        readonly property bool unavailable: tile.meta.available === false
        signal clicked()
        implicitWidth: 64
        implicitHeight: 46
        radius: CairnTheme.radiusSm
        opacity: tile.unavailable ? 0.35 : 1
        color: {
            if (tile.unavailable)
                return "transparent";
            if (tile.active)
                return CairnTheme.selection;
            if (tileHover.hovered || tile.mixed)
                return CairnTheme.hover;
            return "transparent";
        }

        Column {
            anchors.centerIn: parent
            spacing: 2
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: (tile.meta.text || "") === ""
                text: tile.meta.glyph || ""
                font.family: CairnTheme.iconFont
                font.pixelSize: 14
                color: tile.active ? CairnTheme.accent : CairnTheme.muted
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                visible: (tile.meta.text || "") !== ""
                text: tile.meta.text || ""
                color: tile.active ? CairnTheme.accent : CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
                font.weight: tile.meta.id === "bold" ? Font.Bold : Font.Normal
                font.italic: tile.meta.id === "italic"
                font.underline: tile.meta.id === "underline"
                font.strikeout: tile.meta.id === "strike"
            }
            Text {
                anchors.horizontalCenter: parent.horizontalCenter
                width: tile.width - 4
                horizontalAlignment: Text.AlignHCenter
                text: tile.meta.label || ""
                color: CairnTheme.faint
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
                elide: Text.ElideRight
            }
        }
        HoverHandler {
            id: tileHover
        }
        TapHandler {
            onTapped: {
                if (!tile.unavailable)
                    tile.clicked();
            }
        }
    }
}
