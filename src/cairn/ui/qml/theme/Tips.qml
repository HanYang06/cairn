// SPDX-FileCopyrightText: 2026 HanYang06
// SPDX-License-Identifier: Apache-2.0

pragma Singleton

import QtQuick

// 全局悬停提示：组件悬停时调用 show(text, item)，停留片刻后在指针附近显示。
QtObject {
    id: tips
    property string text: ""
    property real tipX: 0
    property real tipY: 0
    property bool visible: false
    property var anchorItem: null

    property Timer delay: Timer {
        interval: 550
        onTriggered: {
            if (tips.anchorItem === null)
                return;
            const p = tips.anchorItem.mapToItem(null, tips.anchorItem.width / 2, tips.anchorItem.height);
            tips.tipX = p.x;
            tips.tipY = p.y + 6;
            tips.visible = true;
        }
    }

    function show(message, item) {
        if (!message)
            return;
        if (visible && anchorItem === item)
            return;
        text = message;
        anchorItem = item;
        visible = false;
        delay.restart();
    }

    function hide() {
        delay.stop();
        visible = false;
        anchorItem = null;
    }
}
