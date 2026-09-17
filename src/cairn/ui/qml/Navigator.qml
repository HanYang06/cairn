// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 双态导航：mode = "notes"（真实笔记）| "projects"（仓库形式）| "community"。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: nav
    color: CairnTheme.surface
    property string mode: "notes"
    signal requestNotes()
    signal noteMenuRequested(string oid, real x, real y)
    signal groupMenuRequested(string gid, real x, real y)
    signal groupUnlockRequested(string gid)

    // 多选
    property bool selecting: false
    property var selectedOids: ({})
    // 显示形态
    property bool dense: false
    property var collapsedGids: ({})
    property string editingGid: ""
    // 拖拽载荷
    property string dragKind: ""
    property string dragId: ""

    function selectedCount() {
        let n = 0;
        for (const k in nav.selectedOids) {
            if (nav.selectedOids[k])
                n++;
        }
        return n;
    }
    function isSelected(oid) {
        return nav.selectedOids[oid] === true;
    }
    function toggleSelect(oid) {
        const m = Object.assign({}, nav.selectedOids);
        if (m[oid])
            delete m[oid];
        else
            m[oid] = true;
        nav.selectedOids = m;
    }
    function clearSelection() {
        nav.selectedOids = ({});
    }
    function selectedList() {
        return Object.keys(nav.selectedOids);
    }
    function selectAll() {
        const m = {};
        const ids = backend.visibleNoteOids();
        for (let i = 0; i < ids.length; i++)
            m[ids[i]] = true;
        nav.selectedOids = m;
    }
    function exitSelect() {
        nav.selecting = false;
        nav.clearSelection();
    }

    // ===== 分组树 =====
    function isExpanded(gid) {
        return gid === "" || nav.collapsedGids[gid] !== true;
    }
    function toggleGroup(gid) {
        const m = Object.assign({}, nav.collapsedGids);
        if (m[gid])
            delete m[gid];
        else
            m[gid] = true;
        nav.collapsedGids = m;
        nav.rebuildRows();
    }
    function expandGroup(gid) {
        const m = Object.assign({}, nav.collapsedGids);
        delete m[gid];
        nav.collapsedGids = m;
        nav.rebuildRows();
    }
    function rebuildRows() {
        groupRowsModel.clear();
        nav.walk(backend.groupTree, 0);
    }
    function walk(nodes, depth) {
        const hasGroups = backend.groupChoices.length > 0;
        for (let i = 0; i < nodes.length; ++i) {
            const node = nodes[i];
            if (node.kind === "group") {
                if (node.gid === "" && !hasGroups) {
                    nav.walk(node.children, depth);
                    continue;
                }
                groupRowsModel.append({
                    "rowKind": "group",
                    "gid": node.gid,
                    "oid": "",
                    "title": node.title,
                    "depth": depth,
                    "count": node.count,
                    "locked": node.lock,
                    "hasKey": node.has_key,
                    "unlocked": node.unlocked,
                    "updated": "",
                    "preview": "",
                    "favorite": false,
                    "archived": false
                });
                if (nav.isExpanded(node.gid))
                    nav.walk(node.children, depth + 1);
            } else {
                groupRowsModel.append({
                    "rowKind": "note",
                    "gid": "",
                    "oid": node.oid,
                    "title": node.title,
                    "depth": depth,
                    "count": 0,
                    "locked": false,
                    "hasKey": false,
                    "unlocked": true,
                    "updated": node.updated,
                    "preview": node.preview,
                    "favorite": node.favorite,
                    "archived": node.archived
                });
            }
        }
    }

    ListModel {
        id: groupRowsModel
    }

    Connections {
        target: backend
        function onGroupsChanged() {
            nav.rebuildRows();
        }
        function onCurrentChanged() {
            nav.rebuildRows();
        }
    }

    Component.onCompleted: nav.rebuildRows()

    Rectangle {
        anchors.right: parent.right
        width: 1
        height: parent.height
        color: CairnTheme.border
        opacity: 0.6
    }

    // ============ 笔记导航 ============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "notes"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: "笔记"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
                IconGlyph {
                    glyph: "\uE762"
                    tip: "选择"
                    active: nav.selecting
                    onClicked: {
                        if (nav.selecting)
                            nav.exitSelect();
                        else
                            nav.selecting = true;
                    }
                }
                IconGlyph {
                    glyph: "\uE710"
                    tip: "新建笔记"
                    onClicked: backend.createNote()
                }
                IconGlyph {
                    glyph: "\uE8F4"
                    tip: "新建组"
                    onClicked: backend.createGroup("新组")
                }
                IconGlyph {
                    glyph: nav.dense ? "\uE8FD" : "\uE8A5"
                    tip: nav.dense ? "紧凑显示" : "详细显示"
                    active: nav.dense
                    onClicked: nav.dense = !nav.dense
                }
                IconGlyph {
                    glyph: "\uE7B8"
                    tip: nav.mode === "notes" ? "显示归档" : "归档"
                    active: backend.showArchived
                    onClicked: backend.toggleShowArchived()
                }
            }
        }

        // 组筛选提示条
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 28
            visible: backend.groupFilter !== ""
            color: CairnTheme.selection
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                spacing: CairnTheme.spaceSm
                Text {
                    text: "\uE71C"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 11
                    color: CairnTheme.accent
                }
                Text {
                    text: "只看此组"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    Layout.fillWidth: true
                }
                Text {
                    text: "清除"
                    color: filterClear.containsMouse ? CairnTheme.danger : CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    MouseArea {
                        id: filterClear
                        anchors.fill: parent
                        anchors.margins: -6
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.clearGroupFilter()
                    }
                }
            }
        }

        Item {
            Layout.preferredHeight: CairnTheme.spaceSm
        }

        Text {
            Layout.leftMargin: CairnTheme.spaceMd
            text: backend.showTrash ? "回收站" : "全部笔记"
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.weight: Font.DemiBold
            font.letterSpacing: 0.6
        }

        ListView {
            id: notesList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            model: groupRowsModel
            boundsBehavior: Flickable.StopAtBounds

            // 空白处双击＝新建空笔记（不必回到顶部按钮）。
            TapHandler {
                acceptedButtons: Qt.LeftButton
                onDoubleTapped: backend.createNote()
            }

            delegate: Item {
                id: del
                width: notesList.width
                height: del.isGroup ? (nav.dense ? 26 : 30) : (nav.dense ? 26 : 62)
                property bool dropHover: false
                readonly property bool isGroup: model.rowKind === "group"
                readonly property bool active: !isGroup && model.oid === backend.currentOid
                readonly property int indent: CairnTheme.spaceMd + model.depth * 14 + (nav.selecting && !isGroup ? 22 : 0)

                HoverHandler {
                    id: delHover
                }

                Rectangle {
                    anchors.fill: parent
                    color: (del.active || (!isGroup && nav.isSelected(model.oid))) ? CairnTheme.selection : (delHover.hovered ? CairnTheme.hover : "transparent")
                }

                Rectangle {
                    anchors.fill: parent
                    visible: del.dropHover
                    color: "transparent"
                    border.color: CairnTheme.accent
                    border.width: 1
                }

                Rectangle {
                    visible: nav.selecting && !del.isGroup
                    x: CairnTheme.spaceMd
                    anchors.verticalCenter: parent.verticalCenter
                    width: 16
                    height: 16
                    radius: 4
                    color: nav.isSelected(model.oid) ? CairnTheme.accent : "transparent"
                    border.color: nav.isSelected(model.oid) ? CairnTheme.accent : CairnTheme.border
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        visible: nav.isSelected(model.oid)
                        text: "\uE73E"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 9
                        color: CairnTheme.accentText
                    }
                }

                // ===== 组行 =====
                Row {
                    visible: del.isGroup
                    x: del.indent
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 5
                    Text {
                        text: nav.isExpanded(model.gid) ? "\uE70D" : "\uE76C"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 9
                        color: CairnTheme.faint
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        text: (model.locked || (model.hasKey && !model.unlocked)) ? "\uE72E" : "\uE8B7"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 12
                        color: CairnTheme.muted
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    Text {
                        visible: nav.editingGid !== model.gid
                        text: model.title
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        font.weight: Font.Medium
                        anchors.verticalCenter: parent.verticalCenter
                    }
                    TextInput {
                        visible: nav.editingGid === model.gid
                        text: model.title
                        width: 120
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        selectByMouse: true
                        onVisibleChanged: {
                            if (visible) {
                                forceActiveFocus();
                                selectAll();
                            }
                        }
                        onEditingFinished: {
                            backend.renameGroup(model.gid, text);
                            nav.editingGid = "";
                        }
                        Keys.onEscapePressed: nav.editingGid = ""
                    }
                    Text {
                        text: "" + model.count
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        anchors.verticalCenter: parent.verticalCenter
                    }
                }

                // 悬停：把当前笔记加进该组
                Text {
                    visible: del.isGroup && model.gid !== "" && (delHover.hovered || addMa.containsMouse) && backend.currentOid !== ""
                    anchors.right: parent.right
                    anchors.rightMargin: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    text: "\uE710"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 11
                    color: addMa.containsMouse ? CairnTheme.accent : CairnTheme.faint
                    MouseArea {
                        id: addMa
                        anchors.fill: parent
                        anchors.margins: -6
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.addNoteToGroup(backend.currentOid, model.gid)
                    }
                }

                // ===== 笔记行 =====
                Column {
                    visible: !del.isGroup
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: del.indent
                    anchors.rightMargin: CairnTheme.spaceMd
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    RowLayout {
                        width: parent.width
                        spacing: 5
                        Text {
                            visible: model.favorite
                            text: "\uE735"
                            color: CairnTheme.accent
                            font.family: CairnTheme.iconFont
                            font.pixelSize: 10
                            Layout.alignment: Qt.AlignVCenter
                        }
                        Text {
                            text: model.title
                            color: model.archived ? CairnTheme.faint : CairnTheme.text
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsSmall
                            font.weight: Font.Medium
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                        Text {
                            text: model.archived ? "已归档" : model.updated
                            color: CairnTheme.faint
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                        }
                    }
                    Text {
                        visible: !nav.dense
                        width: parent.width
                        text: model.preview !== "" ? model.preview : "空笔记"
                        color: model.archived ? CairnTheme.faint : CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        maximumLineCount: 1
                        elide: Text.ElideRight
                    }
                }

                MouseArea {
                    id: delMa
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    drag.target: dragGhost
                    drag.threshold: 8
                    onPressed: {
                        nav.dragKind = del.isGroup ? "group" : "note";
                        nav.dragId = del.isGroup ? model.gid : model.oid;
                    }
                    onReleased: {
                        nav.dragKind = "";
                        nav.dragId = "";
                    }
                    onDoubleClicked: function (mouse) {
                        if (del.isGroup && model.gid !== "" && mouse.button === Qt.LeftButton)
                            nav.editingGid = model.gid;
                    }
                    onClicked: function (mouse) {
                        if (del.isGroup) {
                            if (mouse.button === Qt.RightButton) {
                                if (model.gid === "")
                                    return;
                                const gp = delMa.mapToItem(nav, mouse.x, mouse.y);
                                nav.groupMenuRequested(model.gid, gp.x, gp.y);
                            } else if (model.hasKey && !model.unlocked) {
                                nav.groupUnlockRequested(model.gid);
                            } else {
                                nav.toggleGroup(model.gid);
                            }
                        } else if (mouse.button === Qt.RightButton) {
                            const p = delMa.mapToItem(nav, mouse.x, mouse.y);
                            nav.noteMenuRequested(model.oid, p.x, p.y);
                        } else if (nav.selecting) {
                            nav.toggleSelect(model.oid);
                        } else {
                            backend.openNote(model.oid);
                        }
                    }
                }

                // 拖拽落点：把笔记 / 组拖到组上
                DropArea {
                    anchors.fill: parent
                    enabled: del.isGroup
                    keys: ["cairn-item"]
                    onEntered: del.dropHover = true
                    onExited: del.dropHover = false
                    onDropped: {
                        if (nav.dragKind === "note" && nav.dragId !== "") {
                            if (model.gid === "")
                                backend.clearNoteGroups(nav.dragId);
                            else
                                backend.addNoteToGroup(nav.dragId, model.gid);
                        } else if (nav.dragKind === "group" && nav.dragId !== "" && nav.dragId !== model.gid) {
                            backend.moveGroup(nav.dragId, model.gid);
                        }
                        nav.dragKind = "";
                        nav.dragId = "";
                        del.dropHover = false;
                    }
                }

                // 拖拽时跟手的幽灵
                Item {
                    id: dragGhost
                    width: 150
                    height: 24
                    z: 300
                    visible: delMa.drag.active
                    Drag.active: delMa.drag.active
                    Drag.keys: ["cairn-item"]
                    Drag.hotSpot: Qt.point(width / 2, height / 2)
                    Rectangle {
                        anchors.fill: parent
                        radius: CairnTheme.radiusSm
                        color: CairnTheme.elevated
                        border.color: CairnTheme.accent
                        border.width: 1
                        Text {
                            anchors.centerIn: parent
                            width: parent.width - 12
                            text: model.title
                            color: CairnTheme.text
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                            elide: Text.ElideRight
                            horizontalAlignment: Text.AlignHCenter
                        }
                    }
                }
            }
        }

        // 批量操作条
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            visible: nav.selecting
            color: CairnTheme.chrome
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: CairnTheme.borderFaint
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                spacing: CairnTheme.spaceSm
                Text {
                    text: "已选 " + nav.selectedCount() + " 项"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    Layout.fillWidth: true
                }
                SelectAction {
                    label: "全选"
                    onTapped: nav.selectAll()
                }
                SelectAction {
                    label: "收藏"
                    onTapped: backend.favoriteMany(nav.selectedList())
                }
                SelectAction {
                    label: "回收"
                    onTapped: {
                        backend.trashMany(nav.selectedList());
                        nav.clearSelection();
                    }
                }
                SelectAction {
                    label: "完成"
                    onTapped: nav.exitSelect()
                }
            }
        }

        // 回收站入口：删除先进这里，避免每次确认。
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: backend.showTrash ? CairnTheme.selection : (trashMa.containsMouse ? CairnTheme.hover : "transparent")
            Rectangle {
                anchors.top: parent.top
                width: parent.width
                height: 1
                color: CairnTheme.borderFaint
            }
            MouseArea {
                id: trashMa
                anchors.fill: parent
                hoverEnabled: true
                onClicked: backend.toggleShowTrash()
            }
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                spacing: CairnTheme.spaceSm
                Text {
                    text: "\uE74D"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 12
                    color: backend.showTrash ? CairnTheme.accent : CairnTheme.muted
                }
                Text {
                    text: "回收站"
                    color: backend.showTrash ? CairnTheme.text : CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    Layout.fillWidth: true
                }
                Text {
                    visible: backend.trashedCount > 0
                    text: "" + backend.trashedCount
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                }
                Text {
                    visible: backend.showTrash && backend.trashedCount > 0
                    text: "清空"
                    color: clearMa.containsMouse ? CairnTheme.danger : CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    MouseArea {
                        id: clearMa
                        anchors.fill: parent
                        anchors.margins: -6
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: backend.emptyTrash()
                    }
                }
            }
        }
    }
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "projects"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: "项目"
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

        ListView {
            id: repoList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            spacing: 2
            model: [
                {
                    "name": "Cairn 客户端",
                    "line": "main · 活跃 · 24 节点",
                    "state": "active"
                },
                {
                    "name": "石堆设计",
                    "line": "draft · 8 节点",
                    "state": "draft"
                },
                {
                    "name": "个人知识库",
                    "line": "main · 归档 · 132 节点",
                    "state": "idle"
                },
                {
                    "name": "论文：本地优先",
                    "line": "reading · 41 节点",
                    "state": "active"
                }
            ]
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                width: repoList.width - CairnTheme.spaceMd * 2
                x: CairnTheme.spaceMd
                height: 58
                radius: CairnTheme.radius
                color: repoMa.containsMouse ? CairnTheme.hover : "transparent"
                Behavior on color {
                    ColorAnimation {
                        duration: CairnTheme.durFast
                    }
                }

                Rectangle {
                    id: repoIcon
                    width: 30
                    height: 30
                    radius: CairnTheme.radiusSm
                    anchors.left: parent.left
                    anchors.leftMargin: 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: CairnTheme.elevated
                    Text {
                        anchors.centerIn: parent
                        text: "\uE8B7"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 14
                        color: CairnTheme.accent
                    }
                }
                Column {
                    anchors.left: repoIcon.right
                    anchors.leftMargin: CairnTheme.spaceSm
                    anchors.right: stateDot.left
                    anchors.rightMargin: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text {
                        text: modelData.name
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        font.weight: Font.Medium
                        width: parent.width
                        elide: Text.ElideRight
                    }
                    Text {
                        text: modelData.line
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        width: parent.width
                        elide: Text.ElideRight
                    }
                }
                Rectangle {
                    id: stateDot
                    width: 6
                    height: 6
                    radius: 3
                    anchors.right: parent.right
                    anchors.rightMargin: 4
                    anchors.top: parent.top
                    anchors.topMargin: CairnTheme.spaceSm
                    color: modelData.state === "active" ? CairnTheme.accentAlt : CairnTheme.faint
                }
                MouseArea {
                    id: repoMa
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
        }
    }

    // ============ 社区导航 ============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "community"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                Text {
                    text: "社区"
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

        ListView {
            id: communityList
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: 4
            clip: true
            spacing: 2
            model: [
                {
                    "name": "Cairn 中文",
                    "line": "1,204 成员 · 12 版块",
                    "state": "active"
                },
                {
                    "name": "本地优先软件",
                    "line": "560 成员 · 6 版块",
                    "state": "active"
                },
                {
                    "name": "开源设计",
                    "line": "318 成员 · 4 版块",
                    "state": "idle"
                }
            ]
            boundsBehavior: Flickable.StopAtBounds

            delegate: Rectangle {
                width: communityList.width - CairnTheme.spaceMd * 2
                x: CairnTheme.spaceMd
                height: 58
                radius: CairnTheme.radius
                color: commMa.containsMouse ? CairnTheme.hover : "transparent"
                Behavior on color {
                    ColorAnimation {
                        duration: CairnTheme.durFast
                    }
                }

                Rectangle {
                    id: commIcon
                    width: 30
                    height: 30
                    radius: 15
                    anchors.left: parent.left
                    anchors.leftMargin: 2
                    anchors.verticalCenter: parent.verticalCenter
                    color: CairnTheme.elevated
                    border.color: CairnTheme.border
                    border.width: 1
                    Text {
                        anchors.centerIn: parent
                        text: "\uE716"
                        font.family: CairnTheme.iconFont
                        font.pixelSize: 14
                        color: CairnTheme.accent
                    }
                }
                Column {
                    anchors.left: commIcon.right
                    anchors.leftMargin: CairnTheme.spaceSm
                    anchors.right: parent.right
                    anchors.rightMargin: CairnTheme.spaceSm
                    anchors.verticalCenter: parent.verticalCenter
                    spacing: 3
                    Text {
                        text: modelData.name
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        font.weight: Font.Medium
                        width: parent.width
                        elide: Text.ElideRight
                    }
                    Text {
                        text: modelData.line
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        width: parent.width
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    id: commMa
                    anchors.fill: parent
                    hoverEnabled: true
                }
            }
        }
    }

    // ============ 标签 ============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "tags"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                Text {
                    text: "标签"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
            }
        }

        Flow {
            Layout.fillWidth: true
            Layout.leftMargin: CairnTheme.spaceMd
            Layout.rightMargin: CairnTheme.spaceMd
            Layout.topMargin: CairnTheme.spaceSm
            spacing: 6
            Repeater {
                model: backend.allTags
                delegate: Rectangle {
                    width: chipText.implicitWidth + 20
                    height: 24
                    radius: 12
                    color: chipMa.containsMouse ? CairnTheme.selection : CairnTheme.bg
                    border.color: CairnTheme.border
                    border.width: 1
                    Text {
                        id: chipText
                        anchors.centerIn: parent
                        text: modelData
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    MouseArea {
                        id: chipMa
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            backend.filterByTag(modelData);
                            nav.requestNotes();
                        }
                    }
                }
            }
        }
        Text {
            Layout.leftMargin: CairnTheme.spaceMd
            Layout.topMargin: CairnTheme.spaceSm
            visible: backend.allTags.length === 0
            text: "还没有标签"
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
        }
        Item {
            Layout.fillHeight: true
        }
    }

    // ============ 搜索 ============
    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        visible: nav.mode === "search"

        Item {
            Layout.fillWidth: true
            Layout.preferredHeight: 42
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                Text {
                    text: "搜索"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsBody
                    font.weight: Font.DemiBold
                    Layout.fillWidth: true
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: CairnTheme.spaceMd
            Layout.rightMargin: CairnTheme.spaceMd
            Layout.preferredHeight: 32
            radius: CairnTheme.radiusSm
            color: CairnTheme.bg
            border.color: searchInput.activeFocus ? CairnTheme.accent : "transparent"
            border.width: 1
            Text {
                x: 9
                anchors.verticalCenter: parent.verticalCenter
                text: "\uE721"
                font.family: CairnTheme.iconFont
                font.pixelSize: 12
                color: CairnTheme.faint
            }
            TextInput {
                id: searchInput
                x: 28
                width: parent.width - 36
                anchors.verticalCenter: parent.verticalCenter
                clip: true
                color: CairnTheme.text
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
                selectByMouse: true
                onTextChanged: backend.filterNotes(text)
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    visible: searchInput.text === ""
                    text: "搜索标题与正文…"
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                }
            }
        }

        ListView {
            id: searchResults
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.topMargin: CairnTheme.spaceSm
            clip: true
            model: notesModel
            boundsBehavior: Flickable.StopAtBounds
            delegate: Rectangle {
                width: searchResults.width
                height: 56
                color: srMa.containsMouse ? CairnTheme.hover : "transparent"
                Column {
                    anchors.fill: parent
                    anchors.leftMargin: CairnTheme.spaceMd
                    anchors.rightMargin: CairnTheme.spaceMd
                    anchors.topMargin: CairnTheme.spaceSm
                    spacing: 2
                    Text {
                        width: parent.width
                        text: model.title
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        elide: Text.ElideRight
                    }
                    Text {
                        width: parent.width
                        text: model.preview
                        color: CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                        elide: Text.ElideRight
                    }
                }
                MouseArea {
                    id: srMa
                    anchors.fill: parent
                    hoverEnabled: true
                    onClicked: backend.openNote(model.oid)
                }
            }
        }
    }

    component SelectAction: Text {
        id: sa
        property string label: ""
        signal tapped()
        text: sa.label
        color: saMa.containsMouse ? CairnTheme.text : CairnTheme.muted
        font.family: CairnTheme.fontFamily
        font.pixelSize: CairnTheme.fsTiny
        HoverHandler {
            onHoveredChanged: hovered ? Tips.show(sa.label, sa) : Tips.hide()
        }
        MouseArea {
            id: saMa
            anchors.fill: parent
            anchors.margins: -4
            hoverEnabled: true
            cursorShape: Qt.PointingHandCursor
            onClicked: sa.tapped()
        }
    }

    component IconGlyph: Item {
        id: ig
        property string glyph
        property string tip: ""
        property bool active: false
        signal clicked()
        Layout.preferredWidth: 26
        Layout.preferredHeight: 26
        HoverHandler {
            onHoveredChanged: hovered ? Tips.show(ig.tip, ig) : Tips.hide()
        }
        Rectangle {
            anchors.fill: parent
            radius: CairnTheme.radiusSm
            color: ig.active ? CairnTheme.selection : (igMa.containsMouse ? CairnTheme.hover : "transparent")
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
            color: ig.active ? CairnTheme.accent : (igMa.containsMouse ? CairnTheme.text : CairnTheme.muted)
        }
        MouseArea {
            id: igMa
            anchors.fill: parent
            hoverEnabled: true
            onClicked: ig.clicked()
        }
    }
}
