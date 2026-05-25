import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// LogViewer — scrollable log display with level-based coloring
ScrollView {
    id: root
    clip: true

    property var logEntries: []       // array of {timestamp, level, message}
    property string filterLevel: "all"  // all | error | warn | info | debug

    // Cached filtered entries — updated via direct property change handlers
    property var _filteredEntries: []

    function _updateFilter() {
        if (root.filterLevel === "all") {
            _filteredEntries = root.logEntries
        } else {
            _filteredEntries = root.logEntries.filter(function(e) { return e.level === root.filterLevel })
        }
    }

    onLogEntriesChanged: _updateFilter()
    onFilterLevelChanged: _updateFilter()

    ListView {
        id: logList
        width: Math.max(root.width, 680)
        height: Math.max(root.height, logList.contentHeight)
        model: _filteredEntries
        spacing: 2

        delegate: RowLayout {
            width: ListView.view.width
            spacing: Theme.spacingSM

            // Timestamp
            Text {
                text: modelData.timestamp || ""
                font.pixelSize: Theme.fontMini
                font.family: Theme.fontMonospace
                color: Theme.tertiaryText
                Layout.preferredWidth: 70
            }

            // Level badge
            Rectangle {
                implicitWidth: levelText.implicitWidth + Theme.spacingXS
                implicitHeight: 18
                radius: Theme.radiusSM
                color: _levelBgColor

                readonly property color _levelBgColor: {
                    switch (modelData.level) {
                        case "ERROR": return Theme.errorColor
                        case "WARN": return Theme.warningColor
                        case "INFO": return Theme.separatorColor
                        case "DEBUG": return Theme.inputBg
                        default: return Theme.separatorColor
                    }
                }

                Text {
                    id: levelText
                    anchors.centerIn: parent
                    text: modelData.level || "INFO"
                    font.pixelSize: Theme.fontMini
                    font.bold: true
                    color: (modelData.level === "ERROR" || modelData.level === "WARN") ? Theme.backgroundColor : Theme.secondaryText
                }
            }

            // Message
            Text {
                text: modelData.message || ""
                font.pixelSize: Theme.fontCaption
                font.family: Theme.fontMonospace
                color: _msgColor
                Layout.fillWidth: true
                elide: Text.ElideRight
                wrapMode: Text.NoWrap

                readonly property color _msgColor: {
                    switch (modelData.level) {
                        case "ERROR": return Theme.errorColor
                        case "WARN": return Theme.warningColor
                        case "DEBUG": return Theme.tertiaryText
                        default: return Theme.textColor
                    }
                }
            }
        }

        // Auto-scroll to bottom on new entries
        onCountChanged: {
            if (count > 0) {
                positionViewAtIndex(count - 1, ListView.End)
            }
        }
    }

    Component.onCompleted: _updateFilter()
}
