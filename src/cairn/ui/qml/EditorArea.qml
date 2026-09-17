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
        property bool activeOverlong: false
        property string activeLid: ""

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
        ed.loading = false;
        ed.status = "";
        reloadBlocks();
    }

    // ===== 逐行编辑器 =====
    property var lineItems: ({})

    ListModel {
        id: blocksModel
    }

    function reloadBlocks() {
        blocksModel.clear();
        var blocks = backend.currentBlocks;
        for (var i = 0; i < blocks.length; ++i) {
            var block = blocks[i];
            blocksModel.append({
                lid: block.id,
                kind: block.kind,
                text: block.text,
                markerIndex: block.index,
                overlong: block.overlong,
                para: block.para
            });
        }
    }

    function blockById(lid) {
        var blocks = backend.currentBlocks;
        for (var i = 0; i < blocks.length; ++i) {
            if (blocks[i].id === lid)
                return blocks[i];
        }
        return null;
    }

    function escapeHtml(value) {
        return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function styleCss(style) {
        var css = "";
        if (style.bold)
            css += "font-weight:600;";
        if (style.italic)
            css += "font-style:italic;";
        var deco = "";
        if (style.underline)
            deco += "underline ";
        if (style.strike)
            deco += "line-through ";
        if (deco !== "")
            css += "text-decoration:" + deco.trim() + ";";
        if (style.color)
            css += "color:" + style.color + ";";
        return css;
    }

    function toRich(text, styles) {
        if (!styles || styles.length === 0)
            return escapeHtml(text);
        var sorted = styles.slice().sort(function (a, b) {
            return a[0] - b[0];
        });
        var out = "";
        var pos = 0;
        for (var i = 0; i < sorted.length; ++i) {
            var start = sorted[i][0];
            var end = sorted[i][1];
            var style = sorted[i][2];
            if (start > pos)
                out += escapeHtml(text.slice(pos, start));
            out += "<span style=\"" + styleCss(style) + "\">" + escapeHtml(text.slice(start, end)) + "</span>";
            pos = Math.max(pos, end);
        }
        out += escapeHtml(text.slice(pos));
        return out;
    }

    // 重新渲染某一行（样式变化后）并把焦点/选区放回去。
    function focusLine(lid, position, attempt) {
        var root = ed;
        var item = root.lineItems[lid];
        if (!item) {
            // 新行 delegate 可能还没建好，下一拍重试。
            if ((attempt || 0) < 3)
                Qt.callLater(function () { root.focusLine(lid, position, (attempt || 0) + 1); });
            return;
        }
        item.loading = true;
        item.applyRich();
        item.loading = false;
        item.forceActiveFocus();
        item.cursorPosition = Math.max(0, Math.min(position, item.length));
        item.select(item.cursorPosition, item.cursorPosition);
    }

    function refreshLine(lid, start, end) {
        var item = ed.lineItems[lid];
        if (!item)
            return;
        item.loading = true;
        item.applyRich();
        item.loading = false;
        Qt.callLater(function () {
            item.select(start, end);
            item.forceActiveFocus();
        });
    }

    function refreshActiveOverlong() {
        var block = ed.blockById(ed.activeLid);
        ed.activeOverlong = block ? block.overlong : false;
    }

    function headingSize(para) {
        var heading = Number((para && para.heading) || 0);
        if (heading === 1)
            return CairnTheme.fsTitle;
        if (heading === 2)
            return CairnTheme.fsLarge + 4;
        if (heading === 3)
            return CairnTheme.fsLarge;
        return CairnTheme.fsBody;
    }

    function listIndex(index) {
        var count = 1;
        var i = index - 1;
        while (i >= 0) {
            var para = blocksModel.get(i).para || ({});
            if (para.list === "ordered") {
                count += 1;
                i -= 1;
                continue;
            }
            break;
        }
        return count;
    }

    // 跳到超长行行末（并把该行横向滚到最右）
    function jumpToEnd(lid) {
        var item = ed.lineItems[lid];
        if (!item)
            return;
        item.forceActiveFocus();
        item.cursorPosition = item.length;
        var pane = item.parent;
        if (pane && pane.contentX !== undefined)
            pane.contentX = Math.max(0, pane.contentWidth - pane.width);
    }

    // 执行工具：作用于当前行的选区（无选区则整行），再刷新
    function runTool(tid) {
        var item = ed.lineItems[ed.activeLid];
        if (!item)
            return;
        var start = Math.min(item.selectionStart, item.selectionEnd);
        var end = Math.max(item.selectionStart, item.selectionEnd);
        var lid = ed.activeLid;
        var root = ed;
        backend.runTool(tid, lid, start, end);
        root.reloadBlocks();
        Qt.callLater(function () {
            root.focusLine(lid, end);
        });
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

            // ===== 格式工具栏（字级 / 段级两行）=====
            FormatToolbar {
                id: formatBar
                Layout.fillWidth: true
                activeLineId: ed.activeLid
                toolsEnabled: backend.currentOid !== ""
                onToolTriggered: function (tid) {
                    ed.runTool(tid);
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: CairnTheme.borderFaint
                visible: backend.currentOid !== ""
            }

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

                    Column {
                        id: bodyCol
                        width: parent.width
                        spacing: 2

                        Repeater {
                            model: blocksModel
                            delegate: Item {
                                id: lineRoot
                                width: bodyCol.width
                                height: lineFlick.visible ? lineFlick.height : markerChip.height
                                readonly property var para: model.para || ({})
                                readonly property bool isCode: para.block === "code"
                                readonly property bool isQuote: para.block === "quote"
                                readonly property bool noWrap: model.overlong || isCode
                                readonly property int baseIndent: Number(para.level || 0) * 14
                                readonly property int gutter: CairnTheme.spaceMd + baseIndent + (para.list ? 24 : 0)

                                Rectangle {
                                    visible: lineRoot.isQuote && lineFlick.visible
                                    x: CairnTheme.spaceMd + lineRoot.baseIndent
                                    width: 3
                                    height: parent.height
                                    radius: 1.5
                                    color: CairnTheme.accent
                                    opacity: 0.6
                                }

                                Text {
                                    visible: !!lineRoot.para.list && lineFlick.visible
                                    x: CairnTheme.spaceMd + lineRoot.baseIndent
                                    width: 20
                                    anchors.verticalCenter: parent.verticalCenter
                                    horizontalAlignment: Text.AlignRight
                                    text: lineRoot.para.list === "ordered" ? (ed.listIndex(index) + ".") : "•"
                                    color: CairnTheme.muted
                                    font.family: CairnTheme.fontFamily
                                    font.pixelSize: CairnTheme.fsBody
                                }

                                Flickable {
                                    id: lineFlick
                                    visible: model.kind === "text"
                                    x: lineRoot.gutter
                                    width: lineRoot.width - x
                                    height: bodyLine.height
                                    contentWidth: bodyLine.width
                                    contentHeight: height
                                    clip: true
                                    interactive: lineRoot.noWrap
                                    boundsBehavior: Flickable.StopAtBounds

                                    Rectangle {
                                        anchors.fill: parent
                                        visible: lineRoot.isCode
                                        color: CairnTheme.bg
                                        border.color: CairnTheme.borderFaint
                                        border.width: 1
                                        z: -1
                                    }

                                    TextEdit {
                                        id: bodyLine
                                        width: lineRoot.noWrap ? Math.max(lineFlick.width, contentWidth) : lineFlick.width
                                        textFormat: TextEdit.RichText
                                        wrapMode: lineRoot.noWrap ? TextEdit.NoWrap : TextEdit.Wrap
                                        horizontalAlignment: lineRoot.para.align === "center" ? Text.AlignHCenter : (lineRoot.para.align === "right" ? Text.AlignRight : Text.AlignLeft)
                                        selectByMouse: true
                                        color: CairnTheme.text
                                        font.family: lineRoot.isCode ? CairnTheme.monoFont : CairnTheme.fontFamily
                                        font.pixelSize: ed.headingSize(lineRoot.para)
                                        font.weight: lineRoot.para.heading ? Font.DemiBold : Font.Normal
                                        height: Math.max(contentHeight, 22)

                                    property bool loading: true
                                    readonly property string lid: model.lid

                                    function applyRich() {
                                        var block = ed.blockById(lid);
                                        if (block)
                                            text = ed.toRich(block.text, block.styles);
                                    }

                                    function applyStyle(key) {
                                        var start = Math.min(selectionStart, selectionEnd);
                                        var end = Math.max(selectionStart, selectionEnd);
                                        if (end <= start)
                                            return;
                                        backend.toggleLineStyle(lid, start, end, key);
                                        ed.refreshLine(lid, start, end);
                                    }

                                    Component.onCompleted: {
                                        ed.lineItems[lid] = bodyLine;
                                        loading = true;
                                        applyRich();
                                        loading = false;
                                    }
                                    Component.onDestruction: {
                                        if (ed.lineItems[lid] === bodyLine)
                                            delete ed.lineItems[lid];
                                    }

                                    onTextChanged: {
                                        if (loading)
                                            return;
                                        backend.setLineText(lid, getText(0, length));
                                        ed.status = "编辑中…";
                                        if (activeFocus)
                                            ed.refreshActiveOverlong();
                                    }

                                    onActiveFocusChanged: {
                                        if (activeFocus) {
                                            ed.activeLid = lid;
                                            ed.refreshActiveOverlong();
                                        }
                                    }

                                    Keys.onPressed: function (event) {
                                        var editor = ed;
                                        if (event.modifiers & Qt.ControlModifier) {
                                            if (event.key === Qt.Key_B) {
                                                event.accepted = true;
                                                applyStyle("bold");
                                                return;
                                            }
                                            if (event.key === Qt.Key_I) {
                                                event.accepted = true;
                                                applyStyle("italic");
                                                return;
                                            }
                                            if (event.key === Qt.Key_U) {
                                                event.accepted = true;
                                                applyStyle("underline");
                                                return;
                                            }
                                        }
                                        if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                                            event.accepted = true;
                                            var newId = backend.splitLine(lid, cursorPosition);
                                            editor.reloadBlocks();
                                            if (newId)
                                                Qt.callLater(function () { editor.focusLine(newId, 0); });
                                            return;
                                        }
                                        if (event.key === Qt.Key_Backspace
                                                && cursorPosition === 0
                                                && selectionStart === selectionEnd) {
                                            event.accepted = true;
                                            var keep = getText(0, length).length;
                                            var merged = backend.mergeLine(lid);
                                            if (merged) {
                                                editor.reloadBlocks();
                                                Qt.callLater(function () {
                                                    var block = editor.blockById(merged);
                                                    var pos = block ? Math.max(0, block.text.length - keep) : 0;
                                                    editor.focusLine(merged, pos);
                                                });
                                            }
                                            return;
                                        }
                                        if (event.key === Qt.Key_Down && index < blocksModel.count - 1) {
                                            event.accepted = true;
                                            var below = blocksModel.get(index + 1);
                                            var belowBlock = editor.blockById(below.lid);
                                            editor.focusLine(below.lid, Math.min(cursorPosition, belowBlock ? belowBlock.text.length : 0));
                                            return;
                                        }
                                        if (event.key === Qt.Key_Up && index > 0) {
                                            event.accepted = true;
                                            var above = blocksModel.get(index - 1);
                                            var aboveBlock = editor.blockById(above.lid);
                                            editor.focusLine(above.lid, Math.min(cursorPosition, aboveBlock ? aboveBlock.text.length : 0));
                                            return;
                                        }
                                    }
                                }
                                }

                                Rectangle {
                                    id: markerChip
                                    visible: model.kind !== "text"
                                    width: Math.min(parent.width, markerRow.implicitWidth + 24)
                                    height: 26
                                    radius: CairnTheme.radiusSm
                                    color: CairnTheme.elevated
                                    border.color: CairnTheme.border
                                    border.width: 1
                                    Row {
                                        id: markerRow
                                        anchors.centerIn: parent
                                        spacing: 6
                                        Text {
                                            text: model.kind === "canvas" ? "\uE790" : "\uE723"
                                            font.family: CairnTheme.iconFont
                                            font.pixelSize: 11
                                            color: CairnTheme.muted
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                        Text {
                                            text: (model.kind === "canvas" ? "画板" : "附件")
                                                  + (model.markerIndex >= 0 ? " #" + model.markerIndex : "")
                                            font.family: CairnTheme.fontFamily
                                            font.pixelSize: CairnTheme.fsSmall
                                            color: CairnTheme.muted
                                            anchors.verticalCenter: parent.verticalCenter
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // 超长行的「到行末」按钮：出现在编辑区右下空白处。
        Rectangle {
            id: endButton
            objectName: "endButton"
            visible: ed.activeOverlong
            width: 34
            height: 24
            radius: CairnTheme.radiusSm
            color: endMa.containsMouse ? CairnTheme.hover : CairnTheme.elevated
            border.color: CairnTheme.border
            border.width: 1
            z: 50
            x: flick.mapToItem(ed, flick.width, flick.height).x - width - 18
            y: flick.mapToItem(ed, flick.width, flick.height).y - height - 18
            Text {
                anchors.centerIn: parent
                text: "→|"
                color: CairnTheme.muted
                font.family: CairnTheme.monoFont
                font.pixelSize: CairnTheme.fsTiny
            }
            MouseArea {
                id: endMa
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: ed.jumpToEnd(ed.activeLid)
            }
        }

        Shortcut {
            sequence: "Ctrl+S"
            onActivated: {
                backend.saveNow();
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
