import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// SettingsPage — full settings form bound to SettingsModel
Item {
    id: settingsPage

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

            // ===== 通用 =====
            SectionCard {
                width: parent.width
                sectionTitle: "通用"
                ConfigRadioGroup {
                    labelText: "模式"
                    options: [
                        {value: 1, text: "刮削模式"},
                        {value: 2, text: "整理模式"}
                    ]
                    selectedValue: settings.mainMode
                    onSelectedValueChanged: settings.mainMode = selectedValue
                }

                ConfigRadioGroup {
                    labelText: "软链接"
                    options: [
                        {value: 1, text: "开"},
                        {value: 0, text: "关"}
                    ]
                    selectedValue: settings.softLink
                    onSelectedValueChanged: settings.softLink = selectedValue
                }

                ConfigSwitchInt {
                    labelText: "调试模式"
                    intValue: settings.switchDebug
                }

                ConfigSwitchInt {
                    labelText: "检查更新"
                    intValue: settings.updateCheck
                }

                ConfigSwitchInt {
                    labelText: "保存日志"
                    intValue: settings.saveLog
                }

                ConfigRadioGroup {
                    labelText: "失败文件移动"
                    options: [
                        {value: 1, text: "开"},
                        {value: 0, text: "关"}
                    ]
                    selectedValue: settings.failedFileMove
                    onSelectedValueChanged: settings.failedFileMove = selectedValue
                }

                ConfigInput {
                    labelText: "成功输出文件夹"
                    textValue: settings.successOutputFolder
                    onTextValueChanged: settings.successOutputFolder = textValue
                }

                ConfigInput {
                    labelText: "失败输出文件夹"
                    textValue: settings.failedOutputFolder
                    onTextValueChanged: settings.failedOutputFolder = textValue
                }
            }

            // ===== 代理 =====
            SectionCard {
                width: parent.width
                sectionTitle: "代理"
                ConfigRadioGroup {
                    labelText: "代理类型"
                    options: [
                        {value: "no", text: "无"},
                        {value: "http", text: "HTTP"},
                        {value: "socks5", text: "SOCKS5"}
                    ]
                    selectedValue: settings.proxyType
                    onSelectedValueChanged: settings.proxyType = selectedValue
                }

                ConfigInput {
                    labelText: "代理地址"
                    textValue: settings.proxy
                    onTextValueChanged: settings.proxy = textValue
                }

                ConfigSlider {
                    labelText: "超时 (秒)"
                    sliderValue: settings.timeout
                    fromValue: 1
                    toValue: 30
                    onSliderValueChanged: settings.timeout = sliderValue
                }

                ConfigSlider {
                    labelText: "重试次数"
                    sliderValue: settings.retry
                    fromValue: 0
                    toValue: 10
                    onSliderValueChanged: settings.retry = sliderValue
                }
            }

            // ===== 命名规则 =====
            SectionCard {
                width: parent.width
                sectionTitle: "命名规则"
                ConfigInput {
                    labelText: "文件夹名"
                    textValue: settings.folderName
                    onTextValueChanged: settings.folderName = textValue
                }

                ConfigInput {
                    labelText: "媒体命名"
                    textValue: settings.namingMedia
                    onTextValueChanged: settings.namingMedia = textValue
                }

                ConfigInput {
                    labelText: "文件命名"
                    textValue: settings.namingFile
                    onTextValueChanged: settings.namingFile = textValue
                }
            }

            // ===== 媒体 =====
            SectionCard {
                width: parent.width
                sectionTitle: "媒体"
                ConfigInput {
                    labelText: "文件类型"
                    textValue: settings.mediaType
                    onTextValueChanged: settings.mediaType = textValue
                }

                ConfigInput {
                    labelText: "字幕类型"
                    textValue: settings.subType
                    onTextValueChanged: settings.subType = textValue
                }

                ConfigFilePicker {
                    labelText: "媒体路径"
                    textValue: settings.mediaPath
                    onTextValueChanged: settings.mediaPath = textValue
                }
            }

            // ===== 排除 =====
            SectionCard {
                width: parent.width
                sectionTitle: "排除"
                ConfigInput {
                    labelText: "排除文件夹"
                    textValue: settings.escapeFolders
                    onTextValueChanged: settings.escapeFolders = textValue
                }

                ConfigInput {
                    labelText: "排除字符串"
                    textValue: settings.escapeString
                    onTextValueChanged: settings.escapeString = textValue
                }

                ConfigInput {
                    labelText: "排除文字（正则）"
                    textValue: settings.literals
                    onTextValueChanged: settings.literals = textValue
                }
            }

            // ===== 水印 =====
            SectionCard {
                width: parent.width
                sectionTitle: "水印"
                ConfigSwitchInt {
                    labelText: "封面添加水印"
                    intValue: settings.posterMark
                }

                ConfigSwitchInt {
                    labelText: "缩略图添加水印"
                    intValue: settings.thumbMark
                }

                ConfigSlider {
                    labelText: "水印大小"
                    sliderValue: settings.markSize
                    fromValue: 1
                    toValue: 30
                    onSliderValueChanged: settings.markSize = sliderValue
                }

                ConfigCheckbox {
                    id: markSubCheckbox
                    labelText: "SUB"
                    checked: settings.markType.indexOf("SUB") >= 0
                    onCheckedChanged: _updateMarkType()
                }
                ConfigCheckbox {
                    id: markLeakCheckbox
                    labelText: "LEAK"
                    checked: settings.markType.indexOf("LEAK") >= 0
                    onCheckedChanged: _updateMarkType()
                }
                ConfigCheckbox {
                    id: markUncensoredCheckbox
                    labelText: "UNCENSORED"
                    checked: settings.markType.indexOf("UNCENSORED") >= 0
                    onCheckedChanged: _updateMarkType()
                }

                ConfigRadioGroup {
                    labelText: "水印位置"
                    options: [
                        {value: "top_left", text: "左上"},
                        {value: "top_right", text: "右上"},
                        {value: "bottom_left", text: "左下"},
                        {value: "bottom_right", text: "右下"}
                    ]
                    selectedValue: settings.markPos
                    onSelectedValueChanged: settings.markPos = selectedValue
                }
            }

            // ===== 无码 =====
            SectionCard {
                width: parent.width
                sectionTitle: "无码"
                ConfigRadioGroup {
                    labelText: "无码海报"
                    options: [
                        {value: 0, text: "官方"},
                        {value: 1, text: "裁剪"}
                    ]
                    selectedValue: settings.uncensoredPoster
                    onSelectedValueChanged: settings.uncensoredPoster = selectedValue
                }

                ConfigInput {
                    labelText: "无码前缀"
                    textValue: settings.uncensoredPrefix
                    onTextValueChanged: settings.uncensoredPrefix = textValue
                }
            }

            // ===== 下载 =====
            SectionCard {
                width: parent.width
                sectionTitle: "下载"
                ConfigSwitchInt {
                    labelText: "下载 NFO"
                    intValue: settings.nfoDownload
                }

                ConfigSwitchInt {
                    labelText: "下载 Poster"
                    intValue: settings.posterDownload
                }

                ConfigSwitchInt {
                    labelText: "下载 Fanart"
                    intValue: settings.fanartDownload
                }

                ConfigSwitchInt {
                    labelText: "下载 Thumb"
                    intValue: settings.thumbDownload
                }

                ConfigSwitchInt {
                    labelText: "下载 ExtraFanart"
                    intValue: settings.extrafanartDownload
                }

                ConfigInput {
                    labelText: "ExtraFanart 文件夹"
                    textValue: settings.extrafanartFolder
                    onTextValueChanged: settings.extrafanartFolder = textValue
                }
            }

            // ===== Emby =====
            SectionCard {
                width: parent.width
                sectionTitle: "Emby 客户端"
                ConfigInput {
                    labelText: "Emby 地址"
                    textValue: settings.embyUrl
                    onTextValueChanged: settings.embyUrl = textValue
                }

                ConfigInput {
                    labelText: "API Key"
                    textValue: settings.apiKey
                    onTextValueChanged: settings.apiKey = textValue
                }
            }

            // ===== Baidu AI =====
            SectionCard {
                width: parent.width
                sectionTitle: "百度 AI（人脸检测）"
                ConfigInput {
                    labelText: "App ID"
                    textValue: settings.baiduAppId
                    onTextValueChanged: settings.baiduAppId = textValue
                }

                ConfigInput {
                    labelText: "API Key"
                    textValue: settings.baiduApiKey
                    onTextValueChanged: settings.baiduApiKey = textValue
                }

                ConfigInput {
                    labelText: "Secret Key"
                    textValue: settings.baiduSecretKey
                    onTextValueChanged: settings.baiduSecretKey = textValue
                }
            }

            // ===== Buttons =====
            RowLayout {
                width: parent.width
                spacing: Theme.spacingLG

                Item { Layout.fillWidth: true }

                Button {
                    text: "恢复默认"
                    font.pixelSize: Theme.fontBody
                    onClicked: settings.resetToDefaults()
                }

                Button {
                    text: "保存配置"
                    font.pixelSize: Theme.fontBody
                    highlighted: true
                    onClicked: settings.save()
                }
            }

            // Bottom spacer
            Item { implicitHeight: Theme.spacingXL; width: parent.width }
        }
    }

    function _updateMarkType() {
        var parts = []
        if (markSubCheckbox.checked) parts.push("SUB")
        if (markLeakCheckbox.checked) parts.push("LEAK")
        if (markUncensoredCheckbox.checked) parts.push("UNCENSORED")
        settings.markType = parts.join(",")
    }
}
