import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// LogPage — real-time log output with filtering
Item {
    id: logPage

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // ===== Filter bar =====
        Rectangle {
            Layout.fillWidth: true
            Layout.leftMargin: Theme.spacingMD
            Layout.rightMargin: Theme.spacingMD
            Layout.topMargin: Theme.spacingMD
            implicitHeight: Theme.logFilterBarHeight
            color: Theme.cardBg
            radius: Theme.radiusLG

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Theme.spacingMD
                anchors.rightMargin: Theme.spacingMD
                spacing: Theme.spacingXS

                Text {
                    text: "过滤:"
                    font.pixelSize: Theme.fontCaption
                    color: Theme.secondaryText
                }

                // Filter buttons
                Repeater {
                    model: [
                        {value: "all", text: "全部"},
                        {value: "error", text: "错误"},
                        {value: "warn", text: "警告"},
                        {value: "info", text: "信息"},
                        {value: "debug", text: "调试"}
                    ]

                    Button {
                        text: modelData.text
                        font.pixelSize: Theme.fontCaption
                        flat: true
                        palette.buttonText: logPage._logFilter === modelData.value ? Theme.accentColor : Theme.tertiaryText

                        onClicked: {
                            logPage._logFilter = modelData.value
                            logView.filterLevel = modelData.value
                        }
                    }
                }

                Item { Layout.fillWidth: true }

                Button {
                    text: "清空"
                    font.pixelSize: Theme.fontCaption
                    flat: true
                    palette.buttonText: Theme.tertiaryText
                    onClicked: logView.clearAll()
                }

                Button {
                    text: "导出"
                    font.pixelSize: Theme.fontCaption
                    flat: true
                    palette.buttonText: Theme.tertiaryText
                    onClicked: toast.show("导出日志（待实现）")
                }
            }
        }

        // ===== Log content =====
        LogViewer {
            id: logView
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }

    // Log state
    property string _logFilter: "all"
    property int _maxLogEntries: 1000

    function addLogEntry(entry) {
        logView.addEntry(entry)
        // Trim oldest entries if exceeding limit — batch removal for O(n) performance
        var excess = logView.logModel.count - _maxLogEntries
        if (excess > 0) {
            logView.logModel.remove(0, excess)
        }
    }
}
