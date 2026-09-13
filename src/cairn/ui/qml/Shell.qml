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

    // 左侧导航态："notes" | "projects"
    property string navMode: "notes"
    // 工具册抽屉是否展开
    property bool toolDrawerOpen: false
    // 右侧临时显示的内容标题
    property string previewLabel: ""
    // 深浅主题
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
                current: shell.navMode === "projects" ? 1 : (shell.navMode === "community" ? 2 : 0)
                onActivated: function (index) {
                    if (index === 0)
                        shell.navMode = "notes";
                    else if (index === 1)
                        shell.navMode = "projects";
                    else if (index === 2)
                        shell.navMode = "community";
                }
            }
            Navigator {
                Layout.preferredWidth: CairnTheme.sideBarW
                Layout.fillHeight: true
                mode: shell.navMode
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

    // 顶部覆盖式工具册抽屉
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
            if (id === "notes" || id === "projects" || id === "community")
                shell.navMode = id;
            shell.toolDrawerOpen = false;
        }
        onPreview: function (id, label) {
            shell.previewLabel = label;
        }
    }
}
