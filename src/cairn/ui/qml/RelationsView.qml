// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 关系 / 分支历史图：按拓扑深度分层，边为 derived-from，可拖拽、可点开。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: view
    color: CairnTheme.surface

    property var graph: backend.currentGraph
    property var positions: computePositions()
    property var overrides: ({})

    function computePositions() {
        const g = view.graph || {
            "nodes": []
        };
        const nodes = g.nodes || [];
        const byDepth = {};
        for (let i = 0; i < nodes.length; i++) {
            const d = nodes[i].depth;
            if (!byDepth[d])
                byDepth[d] = [];
            byDepth[d].push(nodes[i]);
        }
        const keys = Object.keys(byDepth).map(Number).sort((a, b) => a - b);
        let maxRows = 1;
        for (const k in byDepth)
            maxRows = Math.max(maxRows, byDepth[k].length);
        const colW = 250;
        const rowH = 100;
        const padX = 60;
        const padY = 40;
        const result = {};
        for (let ci = 0; ci < keys.length; ci++) {
            const col = byDepth[keys[ci]];
            const offset = (maxRows - col.length) * rowH / 2;
            for (let j = 0; j < col.length; j++) {
                result[col[j].oid] = {
                    "x": padX + ci * colW,
                    "y": padY + offset + j * rowH
                };
            }
        }
        return result;
    }

    function center(oid) {
        const p = view.overrides[oid] || view.positions[oid];
        if (!p)
            return Qt.point(0, 0);
        return Qt.point(p.x + 90, p.y + 32);
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            color: CairnTheme.bg
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
                    text: "\uE71B"
                    font.family: CairnTheme.iconFont
                    font.pixelSize: 13
                    color: CairnTheme.accentAlt
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: "关系"
                    color: CairnTheme.text
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    font.weight: Font.DemiBold
                    Layout.alignment: Qt.AlignVCenter
                }
                Text {
                    text: backend.currentTitle !== "" ? ("· " + backend.currentTitle) : ""
                    color: CairnTheme.muted
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsSmall
                    Layout.alignment: Qt.AlignVCenter
                }
                Item {
                    Layout.fillWidth: true
                }
                ViewButton {
                    label: "历史"
                    glyph: "\uE81C"
                    onClicked: backend.openHistory(backend.currentOid)
                }
                ViewButton {
                    label: "复刻"
                    glyph: "\uE8F1"
                    onClicked: backend.deriveNote()
                }
            }
        }

        Item {
            id: canvas
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            Canvas {
                id: edges
                anchors.fill: parent
                onWidthChanged: requestPaint()
                onHeightChanged: requestPaint()
                Component.onCompleted: requestPaint()
                Connections {
                    target: view
                    function onPositionsChanged() {
                        edges.requestPaint();
                    }
                }
                Connections {
                    target: backend
                    function onCurrentChanged() {
                        edges.requestPaint();
                    }
                }
                onPaint: {
                    const ctx = getContext("2d");
                    ctx.reset();
                    const g = view.graph;
                    if (!g || !g.edges)
                        return;
                    ctx.lineWidth = 1.6;
                    ctx.strokeStyle = CairnTheme.accent;
                    for (let i = 0; i < g.edges.length; i++) {
                        const e = g.edges[i];
                        const a = view.center(e.from);
                        const b = view.center(e.to);
                        const mx = (a.x + b.x) / 2;
                        ctx.beginPath();
                        ctx.moveTo(a.x, a.y);
                        ctx.bezierCurveTo(mx, a.y, mx, b.y, b.x, b.y);
                        ctx.stroke();
                    }
                }
            }

            Repeater {
                model: view.graph.nodes
                delegate: Rectangle {
                    id: card
                    width: 180
                    height: 64
                    radius: CairnTheme.radius
                    readonly property var ov: view.overrides[modelData.oid]
                    readonly property var base: view.positions[modelData.oid]
                    x: ov ? ov.x : (base ? base.x : 0)
                    y: ov ? ov.y : (base ? base.y : 0)
                    color: CairnTheme.bg
                    border.width: 1
                    border.color: modelData.current ? CairnTheme.accent : CairnTheme.border
                    z: cardDrag.active ? 10 : 1

                    Rectangle {
                        id: dot
                        width: 6
                        height: 6
                        radius: 3
                        x: CairnTheme.spaceMd
                        y: CairnTheme.spaceMd
                        color: modelData.current ? CairnTheme.accent : CairnTheme.muted
                    }
                    Text {
                        anchors.left: dot.right
                        anchors.leftMargin: 6
                        anchors.verticalCenter: dot.verticalCenter
                        text: modelData.current ? "当前" : "笔记"
                        color: CairnTheme.faint
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsTiny
                    }
                    Text {
                        anchors.left: parent.left
                        anchors.leftMargin: CairnTheme.spaceMd
                        anchors.right: parent.right
                        anchors.rightMargin: CairnTheme.spaceMd
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: CairnTheme.spaceMd
                        text: modelData.title
                        color: CairnTheme.text
                        font.family: CairnTheme.fontFamily
                        font.pixelSize: CairnTheme.fsSmall
                        font.weight: Font.Medium
                        elide: Text.ElideRight
                    }
                    DragHandler {
                        id: cardDrag
                        target: null
                        property point start
                        onActiveChanged: {
                            if (active)
                                start = Qt.point(card.x, card.y);
                        }
                        onTranslationChanged: {
                            if (!active)
                                return;
                            const next = Object.assign({}, view.overrides);
                            next[modelData.oid] = {
                                "x": start.x + translation.x,
                                "y": start.y + translation.y
                            };
                            view.overrides = next;
                            edges.requestPaint();
                        }
                    }
                    TapHandler {
                        onTapped: backend.openNote(modelData.oid)
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: view.graph.nodes.length === 0
                text: "没有关系"
                color: CairnTheme.faint
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsSmall
            }
        }
    }

    component ViewButton: Rectangle {
        id: vb
        property string label
        property string glyph
        signal clicked()
        Layout.alignment: Qt.AlignVCenter
        width: vbText.implicitWidth + (glyph !== "" ? 30 : 20)
        height: 28
        radius: 14
        color: vbMa.containsMouse ? CairnTheme.hover : CairnTheme.surface
        border.color: CairnTheme.border
        border.width: 1
        Row {
            anchors.centerIn: parent
            spacing: 5
            Text {
                visible: vb.glyph !== ""
                anchors.verticalCenter: parent.verticalCenter
                text: vb.glyph
                font.family: CairnTheme.iconFont
                font.pixelSize: 11
                color: CairnTheme.muted
            }
            Text {
                id: vbText
                anchors.verticalCenter: parent.verticalCenter
                text: vb.label
                color: CairnTheme.muted
                font.family: CairnTheme.fontFamily
                font.pixelSize: CairnTheme.fsTiny
            }
        }
        MouseArea {
            id: vbMa
            anchors.fill: parent
            hoverEnabled: true
            onClicked: vb.clicked()
        }
    }
}
