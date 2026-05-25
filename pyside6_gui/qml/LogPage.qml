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
            implicitHeight: 44
            color: Theme.cardBg

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
                    onClicked: logPage._logEntries = []
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
            logEntries: logPage._logEntries
            filterLevel: logPage._logFilter
        }
    }

    // Log state
    property string _logFilter: "all"
    property var _logEntries: [
        {timestamp: "10:23:01", level: "INFO", message: "AVDC 启动"},
        {timestamp: "10:23:02", level: "INFO", message: "加载配置: config.ini"},
        {timestamp: "10:23:02", level: "DEBUG", message: "main_mode = 1 (刮削模式)"},
        {timestamp: "10:23:05", level: "INFO", message: "开始处理目录: /Volumes/Data/Movies"},
        {timestamp: "10:23:06", level: "INFO", message: "找到 15 个文件"},
        {timestamp: "10:23:10", level: "INFO", message: "处理: SSIS-123.mp4 → javbus"},
        {timestamp: "10:23:15", level: "INFO", message: "SSIS-123: 刮削成功"},
        {timestamp: "10:23:20", level: "WARN", message: "ABP-456: javbus 超时，尝试 jav321"},
        {timestamp: "10:23:25", level: "ERROR", message: "ABP-456: 所有站点均失败"},
        {timestamp: "10:23:30", level: "INFO", message: "处理: IPX-789.mp4 → javbus"},
        {timestamp: "10:23:35", level: "INFO", message: "IPX-789: 刮削成功"},
    ]
}
