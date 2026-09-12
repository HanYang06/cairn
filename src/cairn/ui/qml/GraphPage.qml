// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 独立的「图谱 / 族谱」页：以图形化方式展示某个节点或项目的关系与派生。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: page
    color: CairnTheme.bg

    property int mode: 0
    property int layoutMode: 0
    property real zoom: 1.0

    // 节点（坐标为画布比例）
    property var graphNodes: [
        {
            "id": "root",
            "title": "石堆设计笔记",
            "kind": "笔记",
            "x": 0.5,
            "y": 0.15,
            "focus": false
        },
        {
            "id": "layout",
            "title": "布局取舍 v1",
            "kind": "笔记",
            "x": 0.32,
            "y": 0.44,
            "focus": false
        },
        {
            "id": "shell",
            "title": "QML 外壳草案",
            "kind": "灵感",
            "x": 0.32,
            "y": 0.74,
            "focus": true
        },
        {
            "id": "storage",
            "title": "存储层设计笔记",
            "kind": "笔记",
            "x": 0.68,
            "y": 0.30,
            "focus": false
        },
        {
            "id": "project",
            "title": "项目：Cairn 客户端",
            "kind": "项目",
            "x": 0.68,
            "y": 0.64,
            "focus": false
        },
        {
            "id": "icon",
            "title": "cairn-icon.svg",
            "kind": "资产",
            "x": 0.87,
            "y": 0.86,
            "focus": false
        }
    ]

    // 边：kind = derived 派生 / ref 参考 / compose 组合
    property var graphEdges: [
        {
            "from": "root",
            "to": "layout",
            "kind": "derived"
        },
        {
            "from": "layout",
            "to": "shell",
            "kind": "derived"
        },
        {
            "from": "root",
            "to": "storage",
            "kind": "ref"
        },
        {
            "from": "project",
            "to": "root",
            "kind": "compose"
        },
        {
            "from": "project",
            "to": "icon",
            "kind": "compose"
        }
    ]

    function nodeById(id) {
        for (let i = 0; i < graphNodes.length; i++)
            if (graphNodes[i].id === id)
                return graphNodes[i];
        return null;
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ---- toolbar ----
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            color: CairnTheme.surface

            Rectangle {
                anchors.bottom: parent.bottom
                width: parent.width
                height: 1
                color: CairnTheme.border
                opacity: 0.6
            }

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: CairnTheme.spaceMd
                anchors.rightMargin: CairnTheme.spaceSm
                spacing: CairnTheme.spaceSm

                Text {
                    text: "\uE72B"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 12
                    color: CairnTheme.muted
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: "项目：Cairn 客户端"
                    color: CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: "›"
                    color: CairnTheme.faint
                    font.pixelSize: CairnTheme.fsSmall
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: "族谱"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    font.weight: Font.DemiBold
                    Layout.alignment: Qt.AlignVCenter
                }

                Item {
                    Layout.preferredWidth: CairnTheme.spaceMd
                }

                Segmented {
                    Layout.alignment: Qt.AlignVCenter
                    labels: ["族谱", "关系", "组合"]
                    current: page.mode
                    onPicked: page.mode = index
                }

                Item {
                    Layout.fillWidth: true
                }

                Text {
                    text: "布局"
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    Layout.alignment: Qt.AlignVCenter
                }
                Segmented {
                    Layout.alignment: Qt.AlignVCenter
                    labels: ["树", "力", "时间"]
                    current: page.layoutMode
                    onPicked: page.layoutMode = index
                }

                Item {
                    Layout.preferredWidth: CairnTheme.spaceSm
                }
                IconGlyph {
                    glyph: "\uE71F"
                }
                Text {
                    text: "100%"
                    color: CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
                    Layout.alignment: Qt.AlignVCenter
                }
                IconGlyph {
                    glyph: "\uE8A3"
                }
            }
        }

        // ---- canvas ----
        Item {
            id: canvas
            Layout.fillWidth: true
            Layout.fillHeight: true

            Canvas {
                id: edges
                anchors.fill: parent
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                Component.onCompleted: requestPaint()

                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    const colors = {
                        "derived": CairnTheme.accent,
                        "ref": CairnTheme.borderStrong,
                        "compose": CairnTheme.accentAlt
                    };
                    const dashes = {
                        "derived": [],
                        "ref": [4, 4],
                        "compose": [2, 3]
                    };
                    for (let i = 0; i < page.graphEdges.length; i++) {
                        const e = page.graphEdges[i];
                        const a = page.nodeById(e.from);
                        const b = page.nodeById(e.to);
                        if (!a || !b)
                            continue;
                        const ax = a.x * width, ay = a.y * height;
                        const bx = b.x * width, by = b.y * height;
                        const mx = (ax + bx) / 2;
                        ctx.beginPath();
                        ctx.lineWidth = 1.5;
                        ctx.strokeStyle = colors[e.kind];
                        ctx.globalAlpha = e.kind === "ref" ? 0.6 : 0.9;
                        ctx.setLineDash(dashes[e.kind]);
                        ctx.moveTo(ax, ay);
                        ctx.bezierCurveTo(mx, ay, mx, by, bx, by);
                        ctx.stroke();
                        ctx.globalAlpha = 1.0;
                    }
                }
            }

            Repeater {
                model: page.graphNodes
                delegate: NodeCard {
                    width: 190
                    height: 66
                    x: modelData.x * canvas.width - width / 2
                    y: modelData.y * canvas.height - height / 2
                    title: modelData.title
                    kind: modelData.kind
                    focused: modelData.focus
                }
            }

            // legend
            Rectangle {
                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.margins: CairnTheme.spaceLg
                radius: CairnTheme.radius
                color: Qt.rgba(0, 0, 0, 0.25)
                border.color: CairnTheme.border
                border.width: 1
                width: legendRow.implicitWidth + CairnTheme.spaceMd * 2
                height: 34
                Row {
                    id: legendRow
                    anchors.centerIn: parent
                    spacing: CairnTheme.spaceMd
                    Repeater {
                        model: [
                            {
                                "c": CairnTheme.accent,
                                "t": "派生"
                            },
                            {
                                "c": CairnTheme.borderStrong,
                                "t": "参考"
                            },
                            {
                                "c": CairnTheme.accentAlt,
                                "t": "组合"
                            }
                        ]
                        delegate: Row {
                            spacing: 6
                            Rectangle {
                                width: 16
                                height: 2
                                color: modelData.c
                                anchors.verticalCenter: parent.verticalCenter
                            }
                            Text {
                                text: modelData.t
                                color: CairnTheme.muted
                                font.family: CairnTheme.fontFamily
                                font.pixelSize: CairnTheme.fsTiny
                            }
                        }
                    }
                }
            }
        }
    }

    component Segmented: Rectangle {
        id: seg
        property var labels: []
        property int current: 0
        signal picked(int index)
        implicitWidth: segRow.implicitWidth + 4
        implicitHeight: 28
        radius: CairnTheme.radiusSm
        color: CairnTheme.bg
        border.color: CairnTheme.border
        border.width: 1
        Row {
            id: segRow
            anchors.centerIn: parent
            Repeater {
                model: seg.labels
                delegate: Rectangle {
                    width: segLabel.implicitWidth + 20
                    height: 24
                    radius: CairnTheme.radiusSm - 1
                    color: index === seg.current ? CairnTheme.elevated : "transparent"
                    Text {
                        id: segLabel
                        anchors.centerIn: parent
                        text: modelData
                        color: index === seg.current ? CairnTheme.text : CairnTheme.muted
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    MouseArea {
                        anchors.fill: parent
                        onClicked: seg.picked(index)
                    }
                }
            }
        }
    }

    component NodeCard: Rectangle {
        id: card
        property string title: ""
        property string kind: "笔记"
        property bool focused: false
        radius: CairnTheme.radiusLg
        color: CairnTheme.surface
        border.width: 1
        border.color: card.focused ? CairnTheme.accent : CairnTheme.border

        Rectangle {
            id: kindDot
            width: 6
            height: 6
            radius: 3
            anchors.left: parent.left
            anchors.leftMargin: CairnTheme.spaceMd
            anchors.top: parent.top
            anchors.topMargin: CairnTheme.spaceMd
            color: card.kind === "项目" ? CairnTheme.accentAlt : (card.kind === "资产" ? CairnTheme.borderStrong : CairnTheme.accent)
        }
        Text {
            anchors.left: kindDot.right
            anchors.leftMargin: 6
            anchors.verticalCenter: kindDot.verticalCenter
            text: card.kind
            color: CairnTheme.faint
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsTiny
            font.letterSpacing: 0.5
        }
        Text {
            anchors.left: parent.left
            anchors.leftMargin: CairnTheme.spaceMd
            anchors.right: parent.right
            anchors.rightMargin: CairnTheme.spaceMd
            anchors.bottom: parent.bottom
            anchors.bottomMargin: CairnTheme.spaceMd
            text: card.title
            color: CairnTheme.text
            font.family: CairnTheme.fontFamily
            font.pixelSize: CairnTheme.fsSmall
            font.weight: Font.Medium
            elide: Text.ElideRight
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
        }
    }

    component IconGlyph: Item {
        property string glyph
        Layout.preferredWidth: 26
        Layout.preferredHeight: 26
        Text {
            anchors.centerIn: parent
            text: parent.glyph
            font.family: CairnTheme.iconFont
            font.pixelSize: 12
            color: CairnTheme.muted
        }
        MouseArea {
            anchors.fill: parent
            hoverEnabled: true
        }
    }
}
