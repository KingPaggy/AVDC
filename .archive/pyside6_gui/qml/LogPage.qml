import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// LogPage — 实时日志页面，使用 Python 侧过滤的虚拟化模型
// logModel: LogFilterModel 实例（从 main.py 暴露）
// - filterLevel: 过滤级别 (all/error/warn/info/debug)
// - totalCount: 总日志数
// - filteredModel: 过滤后的 QAbstractListModel
// - clearAll(): 清空日志
Item {
    objectName: "logPage"
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
                    font.family: Theme.fontFamilySans
                    font.pixelSize: Theme.fontCaption
                    font.weight: Theme.weightMedium
                    color: Theme.secondaryText
                }

                // Filter buttons — 直接设置 logModel.filterLevel
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
                        font.family: Theme.fontFamilySans
                        font.pixelSize: Theme.fontCaption
                        flat: true
                        palette.buttonText: logModel.filterLevel === modelData.value ? Theme.accentColor : Theme.tertiaryText

                        onClicked: logModel.filterLevel = modelData.value
                    }
                }

                Item { Layout.fillWidth: true }

                // Log count indicator
                Text {
                    text: logModel.totalCount + " 条"
                    font.family: Theme.fontFamilySans
                    font.pixelSize: Theme.fontCaption
                    font.weight: Theme.weightRegular
                    color: Theme.tertiaryText
                    visible: logModel.totalCount > 0
                }

                Button {
                    text: "清空"
                    font.family: Theme.fontFamilySans
                    font.pixelSize: Theme.fontCaption
                    flat: true
                    palette.buttonText: Theme.tertiaryText
                    onClicked: logModel.clearAll()
                }

                Button {
                    text: "导出"
                    font.family: Theme.fontFamilySans
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
            Layout.leftMargin: Theme.spacingMD
            Layout.rightMargin: Theme.spacingMD
            Layout.topMargin: Theme.spacingSM
            Layout.bottomMargin: Theme.spacingMD
        }
    }

    // ===== 连接 logBridge 信号（备用，已由 Python main.py 连接） =====
    // main.py 中: log_bridge.logReceived.connect(log_model.addEntry)
    // 这里不需要再处理，logModel 自动接收日志
}