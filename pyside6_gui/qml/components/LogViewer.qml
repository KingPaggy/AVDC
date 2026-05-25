import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// LogViewer — scrollable log display with level-based coloring
ScrollView {
    id: root
    clip: true

    property var logEntries: []       // array of {timestamp, level, message}
    property string filterLevel: "all"  // all | error | warn | info | debug

    readonly property color _colorError: "#f38ba8"    // Red
    readonly property color _colorWarn: "#f9e2af"     // Yellow
    readonly property color _colorInfo: "#cdd6f4"     // Text
    readonly property color _colorDebug: "#6c7086"    // Overlay2
    readonly property color _colorTimestamp: "#6c7086" // Overlay2

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
            spacing: 8

            // Timestamp
            Text {
                text: modelData.timestamp || ""
                font.pixelSize: 12
                font.family: "monospace"
                color: root._colorTimestamp
                Layout.preferredWidth: 70
            }

            // Level badge
            Rectangle {
                implicitWidth: levelText.implicitWidth + 8
                implicitHeight: 18
                radius: 4
                color: _levelBgColor

                readonly property color _levelBgColor: {
                    switch (modelData.level) {
                        case "ERROR": return "#f38ba8"  // Red
                        case "WARN": return "#f9e2af"   // Yellow
                        case "INFO": return "#45475a"   // Surface1
                        case "DEBUG": return "#313244"  // Surface0
                        default: return "#45475a"
                    }
                }

                Text {
                    id: levelText
                    anchors.centerIn: parent
                    text: modelData.level || "INFO"
                    font.pixelSize: 11
                    font.bold: true
                    color: (modelData.level === "ERROR" || modelData.level === "WARN") ? "#181825" : "#bac2de"
                }
            }

            // Message
            Text {
                text: modelData.message || ""
                font.pixelSize: 13
                font.family: "monospace"
                color: _msgColor
                Layout.fillWidth: true
                elide: Text.ElideRight
                wrapMode: Text.NoWrap

                readonly property color _msgColor: {
                    switch (modelData.level) {
                        case "ERROR": return root._colorError
                        case "WARN": return root._colorWarn
                        case "DEBUG": return root._colorDebug
                        default: return root._colorInfo
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
