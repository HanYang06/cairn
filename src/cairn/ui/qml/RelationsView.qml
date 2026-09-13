// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

// 关系图（竖排，参照 Git 图）：左侧是泳道（分叉 / 固定 / 合并），右侧是整行卡片。
// 位置由拓扑与时序算出，不自由拖拽——线条与文字各占其位，互不遮挡。
import QtQuick
import QtQuick.Layouts
import "theme"

Rectangle {
    id: view
    color: CairnTheme.surface

    property var graph: backend.currentGraph
    property var layout: compute()

    function rootDepth() {
        const nodes = (view.graph && view.graph.nodes) || [];
        for (let i = 0; i < nodes.length; i++) {
            if (nodes[i].current)
                return nodes[i].depth || 0;
        }
        return 0;
    }

    function compute() {
        const g = view.graph || {
            "nodes": [],
            "edges": []
        };
        const nodes = (g.nodes || []).slice();
        const edges = g.edges || [];
        const rootD = view.rootDepth();

        // child -> [parent]
        const parentsOf = {};
        for (let i = 0; i < nodes.length; i++)
            parentsOf[nodes[i].oid] = [];
        for (let i = 0; i < edges.length; i++) {
            if (parentsOf[edges[i].from] === undefined)
                parentsOf[edges[i].from] = [];
            parentsOf[edges[i].from].push(edges[i].to);
        }

        // 时序：旧的在上（来源在上，派生在下）
        nodes.sort(function (a, b) {
            return (a.ts || 0) - (b.ts || 0);
        });

        // Git 式泳道分配：优先复用父节点所在泳道，否则开新道。
        const laneTips = [];
        const laneOf = {};
        for (let i = 0; i < nodes.length; i++) {
            const oid = nodes[i].oid;
            const ps = parentsOf[oid] || [];
            let lane = -1;
            for (let j = 0; j < laneTips.length; j++) {
                if (laneTips[j] !== undefined && ps.indexOf(laneTips[j]) >= 0) {
                    lane = j;
                    break;
                }
            }
            if (lane < 0) {
                lane = laneTips.indexOf(undefined);
                if (lane < 0) {
                    lane = laneTips.length;
                    laneTips.push(undefined);
                }
            }
            laneTips[lane] = oid;
            laneOf[oid] = lane;
            for (let j = 0; j < laneTips.length; j++) {
                if (j !== lane && laneTips[j] !== undefined && ps.indexOf(laneTips[j]) >= 0)
                    laneTips[j] = undefined;
            }
        }

        let maxLane = 0;
        for (const k in laneOf)
            maxLane = Math.max(maxLane, laneOf[k]);

        const rowH = 56;
        const laneW = 26;
        const gutter = 24;
        const items = [];
        const byOid = {};
        for (let i = 0; i < nodes.length; i++) {
            const n = nodes[i];
            let origin = "";
            for (let j = 0; j < edges.length; j++) {
                if (edges[j].from === n.oid) {
                    origin = "复刻自 v" + (edges[j].at || "?");
                    break;
                }
            }
            const role = n.current ? "当前" : ((n.depth || 0) < rootD ? "来源" : "派生");
            const it = {
                "oid": n.oid,
                "title": n.title,
                "role": role,
                "author": n.author,
                "updated": n.updated,
                "current": n.current,
                "origin": origin,
                "x": gutter + laneOf[n.oid] * laneW,
                "y": i * rowH + rowH / 2
            };
            items.push(it);
            byOid[n.oid] = it;
        }
        return {
            "items": items,
            "edges": edges,
            "byOid": byOid,
            "rowH": rowH,
            "cardsX": gutter + (maxLane + 1) * laneW + 8
        };
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
                color: CairnTheme.borderFaint
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
                Text {
                    text: "线＝衍生关系"
                    color: CairnTheme.faint
                    font.family: CairnTheme.fontFamily
                    font.pixelSize: CairnTheme.fsTiny
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

        Flickable {
            id: flick
            Layout.fillWidth: true
            Layout.fillHeight: true
            contentWidth: width
            contentHeight: Math.max(content.height, height)
            clip: true

            Item {
                id: content
                width: flick.width
                height: view.layout.items.length * view.layout.rowH + 40

                Canvas {
                    id: edges
                    anchors.fill: parent
                    onWidthChanged: requestPaint()
                    onHeightChanged: requestPaint()
                    Component.onCompleted: requestPaint()
                    Connections {
                        target: view
                        function onLayoutChanged() {
                            edges.requestPaint();
                        }
                    }
                    onPaint: {
                        const ctx = getContext("2d");
                        ctx.reset();
                        const L = view.layout;
                        ctx.lineCap = "round";
                        ctx.lineJoin = "round";
                        // 边：竖直切线入园的平滑曲线（Git 式），避免直角"蚯蚓"。
                        for (let i = 0; i < L.edges.length; i++) {
                            const e = L.edges[i];
                            const a = L.byOid[e.from];
                            const b = L.byOid[e.to];
                            if (!a || !b)
                                continue;
                            ctx.lineWidth = a.current || b.current ? 2.4 : 1.6;
                            ctx.strokeStyle = (a.current || b.current) ? CairnTheme.accent : CairnTheme.borderStrong;
                            ctx.beginPath();
                            ctx.moveTo(a.x, a.y);
                            if (a.x === b.x) {
                                ctx.lineTo(b.x, b.y);
                            } else {
                                const midY = (a.y + b.y) / 2;
                                ctx.bezierCurveTo(a.x, midY, b.x, midY, b.x, b.y);
                            }
                            ctx.stroke();
                        }
                        // 节点
                        for (let i = 0; i < L.items.length; i++) {
                            const it = L.items[i];
                            ctx.beginPath();
                            ctx.fillStyle = CairnTheme.surface;
                            ctx.arc(it.x, it.y, 5, 0, 6.2831853);
                            ctx.fill();
                            ctx.beginPath();
                            ctx.fillStyle = it.current ? CairnTheme.accent : CairnTheme.muted;
                            ctx.arc(it.x, it.y, it.current ? 4 : 3.2, 0, 6.2831853);
                            ctx.fill();
                        }
                    }
                }

                Repeater {
                    model: view.layout.items
                    delegate: Rectangle {
                        id: card
                        x: view.layout.cardsX
                        y: modelData.y - view.layout.rowH / 2 + 6
                        width: Math.max(120, content.width - view.layout.cardsX - 24)
                        height: view.layout.rowH - 12
                        radius: CairnTheme.radius
                        color: CairnTheme.bg
                        border.color: modelData.current ? CairnTheme.accent : CairnTheme.border
                        border.width: 1
                        z: 2

                        Text {
                            id: role
                            x: CairnTheme.spaceMd
                            width: 36
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.role
                            color: modelData.current ? CairnTheme.accent : CairnTheme.faint
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                        }
                        Text {
                            anchors.left: role.right
                            anchors.leftMargin: 8
                            anchors.right: meta.left
                            anchors.rightMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            text: modelData.title
                            color: CairnTheme.text
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsSmall
                            font.weight: Font.Medium
                            elide: Text.ElideRight
                        }
                        Text {
                            id: meta
                            anchors.right: parent.right
                            anchors.rightMargin: CairnTheme.spaceMd
                            anchors.verticalCenter: parent.verticalCenter
                            text: (modelData.origin !== "" ? modelData.origin + " · " : "") + "作者 " + (modelData.author !== "" ? modelData.author : "—") + " · " + modelData.updated
                            color: CairnTheme.faint
                            font.family: CairnTheme.fontFamily
                            font.pixelSize: CairnTheme.fsTiny
                        }
                        TapHandler {
                            onTapped: backend.openNote(modelData.oid)
                        }
                    }
                }
            }

            Text {
                anchors.centerIn: parent
                visible: view.layout.items.length === 0
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
