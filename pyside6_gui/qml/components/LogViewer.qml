import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import AVDC 1.0

// LogViewer — scrollable log display with level-based coloring
ScrollView {
    id: root
    clip: true

    property var logEntries: []       // array of {timestamp, level, message}
    property string filterLevel: "all"  // all | error | warn | info | debug

    ListView {
        id: logList
        width: Math.max(root.width, 680)
        height: Math.max(root.height, logColumn.implicitHeight)
        model: _filteredEntries
        spacing: 2

        readonly property var _filteredEntries: {
            if (root.filterLevel === "all") return root.logEntries
            return root.logEntries.filter(function(e) { return e.level === root.filterLevel })
        }

        delegate: RowLayout {
            width: ListView.view.width
            spacing: Theme.spacingSM

            // Timestamp
            Text {
                text: modelData.timestamp || ""
                font.pixelSize: Theme.fontMini
                font.family: "monospace"
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
                font.family: "monospace"
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
}
