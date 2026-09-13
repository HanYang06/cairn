// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 主窗口内容骨架（与窗口本身解耦，便于离屏预览与复用）。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: shell
    implicitWidth: 1440
    implicitHeight: 900
    color: CairnTheme.bg

    property string navMode: "notes"
    property bool toolDrawerOpen: false
    property bool profileOpen: false
    property string previewLabel: ""
    property bool dark: false

    Binding {
        target: CairnTheme
        property: "dark"
        value: shell.dark
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
                    if (map[index] !== undefined)
                        shell.navMode = map[index];
                }
                onProfileRequested: shell.profileOpen = !shell.profileOpen
            }
            Navigator {
                Layout.preferredWidth: CairnTheme.sideBarW
                Layout.fillHeight: true
                mode: shell.navMode
                onRequestNotes: shell.navMode = "notes"
            }
            EditorArea {
                Layout.fillWidth: true
                Layout.fillHeight: true
            }
            RightDock {
                Layout.preferredWidth: 288
                Layout.fillHeight: true
                mode: shell.navMode
                preview: shell.previewLabel
            }
        }
        StatusBar {
            Layout.fillWidth: true
            Layout.preferredHeight: CairnTheme.statusH
        }
    }

    ToolDrawer {
        id: toolDrawer
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: CairnTheme.titleBarH
        anchors.bottom: parent.bottom
        anchors.bottomMargin: CairnTheme.statusH
        z: 100
        open: shell.toolDrawerOpen
        onLaunch: function (id) {
            if (id === "notes" || id === "projects" || id === "community" || id === "search" || id === "tags") {
                shell.navMode = id;
            } else if (id === "relations" || id === "graph") {
                backend.openRelations();
            } else if (id === "history") {
                backend.openHistory(backend.currentOid);
            }
            shell.toolDrawerOpen = false;
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
}
