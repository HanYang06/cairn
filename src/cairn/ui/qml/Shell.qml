// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 主窗口内容骨架（与窗口本身解耦，便于离屏预览与复用）。
import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import "theme"

Rectangle {
    id: shell
    implicitWidth: 1440
    implicitHeight: 900
    color: CairnTheme.bg

    property string navMode: "notes"
    property bool profileOpen: false
    property string previewLabel: ""
    property bool dark: false

    // ===== 布局契约 =====
    // 三栏都可拖拽改宽；左右两栏可收起；聚焦模式临时收两栏并可还原。
    property bool navOpen: true
    property bool inspectorOpen: false
    property bool focusMode: false
    property bool navOpenBeforeFocus: true
    property bool inspectorOpenBeforeFocus: true

    function toggleNav() {
        if (shell.focusMode)
            shell.focusMode = false;
        shell.navOpen = !shell.navOpen;
    }

    function toggleInspector() {
        if (shell.focusMode)
            shell.focusMode = false;
        shell.inspectorOpen = !shell.inspectorOpen;
    }

    function toggleFocus() {
        if (!shell.focusMode) {
            shell.navOpenBeforeFocus = shell.navOpen;
            shell.inspectorOpenBeforeFocus = shell.inspectorOpen;
            shell.focusMode = true;
        } else {
            shell.focusMode = false;
            shell.navOpen = shell.navOpenBeforeFocus;
            shell.inspectorOpen = shell.inspectorOpenBeforeFocus;
        }
    }

    Binding {
        target: CairnTheme
        property: "dark"
        value: shell.dark
    }

    Shortcut {
        sequence: "Ctrl+B"
        onActivated: shell.toggleNav()
    }
    Shortcut {
        sequence: "Ctrl+Shift+B"
        onActivated: shell.toggleInspector()
    }
    Shortcut {
        sequence: "Ctrl+Shift+Return"
        onActivated: shell.toggleFocus()
    }
    Shortcut {
        sequence: "Escape"
        enabled: shell.focusMode
        onActivated: shell.toggleFocus()
    }
    Shortcut {
        sequence: "Escape"
        enabled: noteMenu.open
        onActivated: noteMenu.close()
    }
    Shortcut {
        sequence: "Escape"
        enabled: sharePopover.open
        onActivated: sharePopover.close()
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0
        TitleBar {
            Layout.fillWidth: true
            Layout.preferredHeight: CairnTheme.titleBarH
        }
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            ActivityBar {
                Layout.preferredWidth: CairnTheme.activityW
                Layout.fillHeight: true
                visible: !shell.focusMode
                current: {
                    if (shell.navMode === "projects")
                        return 1;
                    if (shell.navMode === "community")
                        return 2;
                    if (shell.navMode === "search")
                        return 4;
                    if (shell.navMode === "tags")
                        return 5;
                    return 0;
                }
                onActivated: function (index) {
                    const map = {
                        0: "notes",
                        1: "projects",
                        2: "community",
                        4: "search",
                        5: "tags"
                    };
                    const target = map[index];
                    if (target === undefined)
                        return;
                    if (shell.navMode === target && shell.navOpen) {
                        shell.toggleNav();
                    } else {
                        shell.navMode = target;
                        shell.navOpen = true;
                    }
                }
                onProfileRequested: shell.profileOpen = !shell.profileOpen
            }

            SplitView {
                id: mainSplit
                Layout.fillWidth: true
                Layout.fillHeight: true
                orientation: Qt.Horizontal

                // 分隔条：默认一条细线，悬停/拖拽时变粗并染色；双击收起相邻栏。
                handle: Item {
                    id: splitHandle
                    implicitWidth: 6
                    readonly property bool hot: SplitHandle.hovered
                    readonly property bool down: SplitHandle.pressed

                    Rectangle {
                        anchors.fill: parent
                        color: CairnTheme.hover
                        opacity: splitHandle.hot || splitHandle.down ? 0.7 : 0
                        Behavior on opacity {
                            NumberAnimation {
                                duration: CairnTheme.durFast
                            }
                        }
                    }
                    Rectangle {
                        anchors.centerIn: parent
                        width: splitHandle.hot || splitHandle.down ? 2 : 1
                        height: parent.height
                        color: splitHandle.down ? CairnTheme.accent : (splitHandle.hot ? CairnTheme.borderStrong : CairnTheme.border)
                        opacity: splitHandle.hot || splitHandle.down ? 1 : 0.55
                    }
                }

                Navigator {
                    id: navPane
                    objectName: "navigator"
                    SplitView.preferredWidth: CairnTheme.sideBarW
                    SplitView.minimumWidth: 168
                    SplitView.maximumWidth: 480
                    visible: shell.navOpen && !shell.focusMode
                    mode: shell.navMode
                    onRequestNotes: shell.navMode = "notes"
                    onNoteMenuRequested: function (oid, x, y) {
                        const p = navPane.mapToItem(shell, x, y);
                        noteMenu.openFor(backend.noteInfo(oid), p.x, p.y);
                    }
                }

                EditorArea {
                    id: editorPane
                    SplitView.fillWidth: true
                    SplitView.minimumWidth: 360
                    inspectorOpen: shell.inspectorOpen
                    focusMode: shell.focusMode
                    onToggleInspector: shell.toggleInspector()
                    onShareRequested: function (x, y) {
                        const p = editorPane.mapToItem(shell, x, y);
                        sharePopover.openAt(p.x, p.y);
                    }
                }

                RightDock {
                    id: dockPane
                    SplitView.preferredWidth: 288
                    SplitView.minimumWidth: 220
                    SplitView.maximumWidth: 460
                    visible: shell.inspectorOpen && !shell.focusMode
                    mode: shell.navMode
                    preview: shell.previewLabel
                    onCollapseRequested: shell.toggleInspector()
                }
            }
        }
        StatusBar {
            Layout.fillWidth: true
            Layout.preferredHeight: CairnTheme.statusH
        }
    }

    ToolDrawer {
        id: toolDrawer
        objectName: "toolDrawer"
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.bottomMargin: CairnTheme.statusH
        z: 100
        onLaunch: function (id) {
            if (id === "notes" || id === "projects" || id === "community" || id === "search" || id === "tags") {
                shell.navMode = id;
            } else if (id === "relations" || id === "graph") {
                backend.openRelations();
            } else if (id === "history") {
                backend.openHistory(backend.currentOid);
            }
        }
        onPreview: function (id, label) {
            shell.previewLabel = label;
        }
    }

    ProfileMenu {
        id: profileMenu
        anchors.left: parent.left
        anchors.leftMargin: CairnTheme.activityW + CairnTheme.spaceSm
        anchors.bottom: parent.bottom
        anchors.bottomMargin: CairnTheme.statusH + CairnTheme.spaceSm
        z: 120
        open: shell.profileOpen
        onClosed: shell.profileOpen = false
    }

    // 右键菜单：点空白处关闭 + 菜单本体。
    MouseArea {
        id: menuCatcher
        anchors.fill: parent
        anchors.topMargin: CairnTheme.titleBarH
        z: 190
        visible: noteMenu.open || sharePopover.open
        onClicked: {
            noteMenu.close();
            sharePopover.close();
        }
    }

    NoteMenu {
        id: noteMenu
        objectName: "noteMenu"
        onPicked: function (action) {
            const oid = noteMenu.oid;
            const mx = noteMenu.x;
            const my = noteMenu.y + noteMenu.height;
            noteMenu.close();
            if (action === "open")
                backend.openNote(oid);
            else if (action === "derive")
                backend.deriveFrom(oid);
            else if (action === "favorite")
                backend.toggleFavorite(oid);
            else if (action === "archive")
                backend.toggleArchive(oid);
            else if (action === "share") {
                backend.openNote(oid);
                sharePopover.openAt(mx, my);
            } else if (action === "homepage")
                backend.toggleHomepageOf(oid);
            else if (action === "history")
                backend.openHistory(oid);
            else if (action === "relations") {
                backend.openNote(oid);
                backend.openRelations();
            } else if (action === "trash")
                backend.trashNote(oid);
            else if (action === "restore")
                backend.restoreNote(oid);
            else if (action === "purge")
                backend.purgeNote(oid);
        }
    }

    SharePopover {
        id: sharePopover
        objectName: "sharePopover"
    }
}
