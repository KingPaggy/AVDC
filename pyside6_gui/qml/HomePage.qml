import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// HomePage — workspace: file selection, mode, process button, progress
Item {
    id: homePage

    ScrollView {
        anchors.fill: parent
        clip: true
        contentWidth: width

        Column {
            anchors.horizontalCenter: parent.horizontalCenter
            width: Math.min(parent.width - Theme.spacingXL * 2, Theme.maxContentWidth)
            spacing: Theme.spacingLG

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
                        font.pixelSize: Theme.fontBody
                        highlighted: true
                        Layout.fillWidth: true
                        onClicked: toast.show("开始处理...")
                    }

                    Button {
                        text: "停止"
                        font.pixelSize: Theme.fontBody
                        Layout.fillWidth: true
                        onClicked: toast.show("已停止")
                    }
                }
            }

            // ===== 进度 =====
            SectionCard {
                width: parent.width
                sectionTitle: "进度"
                ProgressBar {
                    progressValue: homePage._demoProgress
                    statusText: homePage._demoStatusText
                    Layout.fillWidth: true
                }

                RowLayout {
                    width: parent.width
                    spacing: Theme.spacingLG

                    StatusBadge { status: "success"; text: "成功: " + homePage._successCount }
                    StatusBadge { status: "error"; text: "失败: " + homePage._errorCount }
                    StatusBadge { status: "info"; text: "跳过: " + homePage._skipCount }
                }
            }
        }
    }

    property real _demoProgress: 0.0
    property string _demoStatusText: ""
    property int _successCount: 0
    property int _errorCount: 0
    property int _skipCount: 0
}
