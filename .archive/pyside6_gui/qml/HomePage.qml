import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// HomePage — workspace: file selection, mode, process button, progress
Item {
    objectName: "homePage"
    id: homePage

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: width

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(parent.width - Theme.spacingXL * 2, Theme.maxContentWidth)
            spacing: Theme.spacingLG

            // Top spacer
            Item { implicitHeight: Theme.spacingXL; width: parent.width }

            // ===== 输入 =====
            SectionCard {
                width: parent.width
                sectionTitle: "输入"
                ConfigFilePicker {
                    labelText: "输入目录"
                    textValue: settings.successOutputFolder
                    onTextValueChanged: settings.successOutputFolder = textValue
                }
                ConfigInput {
                    labelText: "排除文件夹"
                    textValue: settings.escapeFolders
                    onTextValueChanged: settings.escapeFolders = textValue
                }
            }

            // ===== 处理模式 =====
            SectionCard {
                width: parent.width
                sectionTitle: "处理模式"
                ConfigRadioGroup {
                    labelText: "模式"
                    options: [
                        {value: 1, text: "刮削模式"},
                        {value: 2, text: "整理模式"}
                    ]
                    selectedValue: settings.mainMode
                    onSelectedValueChanged: settings.mainMode = selectedValue
                }
            }

            // ===== 操作 =====
            SectionCard {
                width: parent.width
                sectionTitle: "操作"
                RowLayout {
                    width: parent.width
                    spacing: Theme.spacingLG

                    Button {
                        text: "开始处理"
                        font.family: Theme.fontFamilySans
                        font.pixelSize: Theme.fontBody
                        font.weight: Theme.weightMedium
                        highlighted: true
                        enabled: !processing.isProcessing
                        Layout.fillWidth: true
                        onClicked: {
                            var dir = settings.successOutputFolder
                            var escape = settings.escapeFolders
                            var mode = settings.mainMode
                            processing.startBatch(dir, escape, mode)
                        }
                    }

                    Button {
                        text: "停止"
                        font.family: Theme.fontFamilySans
                        font.pixelSize: Theme.fontBody
                        font.weight: Theme.weightMedium
                        enabled: processing.isProcessing
                        Layout.fillWidth: true
                        onClicked: processing.stop()
                    }
                }
            }

            // ===== 进度 =====
            SectionCard {
                width: parent.width
                sectionTitle: "进度"
                ProgressBar {
                    progressValue: processing.progressValue
                    statusText: processing.statusText
                    Layout.fillWidth: true
                }

                RowLayout {
                    width: parent.width
                    spacing: Theme.spacingLG

                    StatusBadge { status: "success"; text: "成功: " + processing.successCount }
                    StatusBadge { status: "error"; text: "失败: " + processing.failCount }
                    StatusBadge { status: "info"; text: "跳过: " + processing.skipCount }
                }
            }

            // Bottom spacer
            Item { implicitHeight: Theme.spacingXL; width: parent.width }
        }
    }

}
