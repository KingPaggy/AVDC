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

        Item {
            anchors.fill: parent

            ColumnLayout {
                id: column
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: 16
                anchors.bottom: parent.bottom
                anchors.bottomMargin: 24
                width: 680
                spacing: 16

                // ===== 输入目录 =====
                SectionCard { sectionTitle: "输入" }

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

                // ===== 模式 =====
                SectionCard { sectionTitle: "处理模式" }

                ConfigRadioGroup {
                    labelText: "模式"
                    options: [
                        {value: 1, text: "刮削模式"},
                        {value: 2, text: "整理模式"}
                    ]
                    selectedValue: settings.mainMode
                    onSelectedValueChanged: settings.mainMode = selectedValue
                }

                // ===== 操作 =====
                SectionCard { sectionTitle: "操作" }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    Button {
                        text: "开始处理"
                        font.pixelSize: 14
                        highlighted: true
                        Layout.fillWidth: true
                        // TODO: wire up to CoreEngine.process_batch()
                        onClicked: {
                            toast.show("开始处理...")
                        }
                    }

                    Button {
                        text: "停止"
                        font.pixelSize: 14
                        Layout.fillWidth: true
                        // TODO: wire up to stop processing
                        onClicked: {
                            toast.show("已停止")
                        }
                    }
                }

                // ===== 进度 =====
                SectionCard { sectionTitle: "进度" }

                ProgressBar {
                    progressValue: _demoProgress
                    statusText: _demoStatusText
                    Layout.fillWidth: true
                }

                // Stats row
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 16

                    StatusBadge { status: "success"; text: "成功: " + _successCount }
                    StatusBadge { status: "error"; text: "失败: " + _errorCount }
                    StatusBadge { status: "info"; text: "跳过: " + _skipCount }
                }
            }
        }
    }

    // Demo state (replace with real CoreEngine bindings)
    property real _demoProgress: 0.35
    property string _demoStatusText: "正在处理: SSIS-123.mp4"
    property int _successCount: 12
    property int _errorCount: 2
    property int _skipCount: 1
}
