import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// LogViewer — 虚拟化日志显示，使用 Qt AbstractListModel
// QML ListView 只渲染可见行，实现真正的虚拟化
ScrollView {
    id: root
    clip: true

    // 绑定到 logModel.filteredModel (QAbstractListModel)
    // 这个 model 由 Python LogFilterModel 管理，已过滤
    property var logModel: logModel.filteredModel

    // 颜色查找表 — 避免 delegate 中的条件判断
    readonly property var _levelColors: ({
        "ERROR": Theme.errorColor,
        "WARN": Theme.warningColor,
        "INFO": Theme.separatorColor,
        "DEBUG": Theme.inputBg
    })
    readonly property var _msgColors: ({
        "ERROR": Theme.errorColor,
        "WARN": Theme.warningColor,
        "DEBUG": Theme.tertiaryText,
        "INFO": Theme.textColor
    })
    readonly property var _levelTextColors: ({
        "ERROR": Theme.backgroundColor,
        "WARN": Theme.backgroundColor,
        "INFO": Theme.secondaryText,
        "DEBUG": Theme.secondaryText
    })

    ListView {
        id: logList
        anchors.fill: parent
        model: root.logModel
        spacing: 2
        clip: true

        // 虚拟化关键参数
        cacheBuffer: 100  // 缓存额外 100px 内容，平滑滚动
        preferredHighlightBegin: -1  // 不需要高亮
        preferredHighlightEnd: -1
        highlightRangeMode: ListView.StrictlyEnforceRange

        // 自动滚动到底部（当有新日志时）
        onCountChanged: {
            if (count > 0 && !atYEnd) {
                // 只有用户没有手动滚动时才自动滚动
                // 使用 Timer 避免频繁调用
                autoScrollTimer.start()
            }
        }

        Timer {
            id: autoScrollTimer
            interval: 50
            onTriggered: logList.positionViewAtEnd()
        }

        delegate: RowLayout {
            width: ListView.view.width
            spacing: Theme.spacingSM

            // Timestamp
            Text {
                text: model.timestamp || ""
                font.family: Theme.fontFamilyMono
                font.pixelSize: Theme.fontMini
                font.weight: Theme.weightRegular
                lineHeight: Theme.lineHeightRelaxed
                lineHeightMode: Text.ProportionalHeight
                color: Theme.tertiaryText
                Layout.preferredWidth: 70
            }

            // Level badge
            Rectangle {
                implicitWidth: levelText.implicitWidth + Theme.spacingXS
                implicitHeight: 18
                radius: Theme.radiusSM
                color: root._levelColors[model.level] !== undefined ? root._levelColors[model.level] : Theme.separatorColor

                Text {
                    id: levelText
                    anchors.centerIn: parent
                    text: model.level || "INFO"
                    font.family: Theme.fontFamilySans
                    font.pixelSize: Theme.fontMini
                    font.weight: Theme.weightSemibold
                    lineHeight: Theme.lineHeightTight
                    lineHeightMode: Text.ProportionalHeight
                    color: root._levelTextColors[model.level] !== undefined ? root._levelTextColors[model.level] : Theme.secondaryText
                }
            }

            // Message
            Text {
                text: model.message || ""
                font.family: Theme.fontFamilyMono
                font.pixelSize: Theme.fontCaption
                font.weight: Theme.weightRegular
                lineHeight: Theme.lineHeightRelaxed
                lineHeightMode: Text.ProportionalHeight
                color: root._msgColors[model.level] !== undefined ? root._msgColors[model.level] : Theme.textColor
                Layout.fillWidth: true
                elide: Text.ElideRight
                wrapMode: Text.NoWrap
            }
        }
    }

    // 滚动到底部的方法（供外部调用）
    function scrollToBottom() {
        logList.positionViewAtEnd()
    }
}