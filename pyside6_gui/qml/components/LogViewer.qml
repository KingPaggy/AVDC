import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// LogViewer — scrollable log display with level-based coloring
ScrollView {
    id: root
    clip: true

    property string filterLevel: "all"  // all | error | warn | info | debug

    // ListModel for O(1) insert/delete without array re-creation
    property var logModel: logListModel

    // Lookup tables for level colors — avoids switch expressions in delegates
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

    function addEntry(entry) {
        logModel.append(entry)
        // Auto-scroll after append
        Qt.callLater(logList.positionViewAtEnd)
    }

    function clearAll() {
        logModel.clear()
    }

    ListModel {
        id: logListModel
    }

    ListView {
        id: logList
        width: Math.max(root.width, Theme.maxContentWidth)
        height: Math.max(root.height, logList.contentHeight)
        model: logListModel
        spacing: 2

        delegate: RowLayout {
            width: ListView.view.width
            spacing: Theme.spacingSM

            // Filter visibility — controlled by root.filterLevel, no array recreation
            visible: root.filterLevel === "all" ||
                     (root.filterLevel === "error" && model.level === "ERROR") ||
                     (root.filterLevel === "warn" && model.level === "WARN") ||
                     (root.filterLevel === "info" && model.level === "INFO") ||
                     (root.filterLevel === "debug" && model.level === "DEBUG")

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
}
