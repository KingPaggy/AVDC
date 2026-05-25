import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// ToolsPage — tool cards in a grid layout
Item {
    id: toolsPage

    ScrollView {
        anchors.fill: parent
        clip: true

        Item {
            anchors.fill: parent

            ColumnLayout {
                id: column
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.top: parent.top
                anchors.topMargin: Theme.spacingXL
                anchors.bottom: parent.bottom
                anchors.bottomMargin: Theme.spacingXL
                width: Math.min(parent.width - Theme.spacingXL * 2, 680)
                spacing: Theme.spacingLG

                // ===== 文件工具 =====
                SectionCard {
                    sectionTitle: "文件工具"
                    GridLayout {
                        width: parent.width
                        columns: 2
                        columnSpacing: Theme.spacingMD
                        rowSpacing: Theme.spacingMD

                        ToolCard {
                            title: "批量重命名"
                            description: "按命名规则批量重命名影片文件"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("批量重命名（待实现）")
                        }

                        ToolCard {
                            title: "封面裁剪"
                            description: "自动裁剪 Poster 和 Thumb 封面图"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("封面裁剪（待实现）")
                        }

                        ToolCard {
                            title: "水印处理"
                            description: "批量添加或去除封面水印"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("水印处理（待实现）")
                        }

                        ToolCard {
                            title: "格式转换"
                            description: "视频格式批量转换（MP4 / MKV）"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("格式转换（待实现）")
                        }
                    }
                }

                // ===== 媒体库工具 =====
                SectionCard {
                    sectionTitle: "媒体库工具"
                    GridLayout {
                        width: parent.width
                        columns: 2
                        columnSpacing: Theme.spacingMD
                        rowSpacing: Theme.spacingMD

                        ToolCard {
                            title: "Emby 同步"
                            description: "同步元数据到 Emby 媒体库"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("Emby 同步（待实现）")
                        }

                        ToolCard {
                            title: "NFO 生成器"
                            description: "手动生成或修复 NFO 元数据文件"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("NFO 生成器（待实现）")
                        }

                        ToolCard {
                            title: "元数据编辑"
                            description: "手动编辑影片元数据信息"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("元数据编辑（待实现）")
                        }

                        ToolCard {
                            title: "重复检测"
                            description: "扫描并去重重复的媒体文件"
                            actionLabel: "打开"
                            Layout.fillWidth: true
                            onClicked: toast.show("重复检测（待实现）")
                        }
                    }
                }
            }
        }
    }
}
