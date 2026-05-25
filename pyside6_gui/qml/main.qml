import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

ApplicationWindow {
    id: appWindow
    visible: true
    width: 960
    height: 700
    minimumWidth: 800
    minimumHeight: 600
    title: "AVDC — PySide6 QML"
    color: "#181825"

    // SettingsModel is exposed from Python as context property "settings"

    // Toast notification
    Rectangle {
        id: toast
        anchors.horizontalCenter: parent.horizontalCenter
        y: -50
        width: toastText.implicitWidth + 40
        height: 40
        radius: 8
        color: "#a6e3a1"
        z: 100
        Behavior on y {
            NumberAnimation { duration: 300; easing.type: Easing.OutCubic }
        }

        Text {
            id: toastText
            anchors.centerIn: parent
            font.pixelSize: 14
            font.bold: true
            color: "#1e1e2e"
        }

        function show(message: string) {
            toastText.text = message
            y = 16
            timer.restart()
        }

        Timer {
            id: timer
            interval: 2000
            onTriggered: y = -50
        }
    }

    // Connections for settings events
    Connections {
        target: settings
        function onConfigSaved() { toast.show("配置已保存") }
        function onConfigLoaded() { toast.show("配置已加载") }
        function onErrorOccurred(msg: string) { toast.show(msg); toast.color = "#f38ba8" }
    }

    // Main layout
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 0
        spacing: 0

        // Content area
        SwipeView {
            id: swipeView
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: tabBar.currentIndex

            // Placeholder: Home
            Item {
                Rectangle {
                    anchors.centerIn: parent
                    color: "#1e1e2e"
                    radius: 12
                    width: 300; height: 100
                    Text {
                        anchors.centerIn: parent
                        text: "主页 — 工作台（待实现）"
                        color: "#6c7086"
                        font.pixelSize: 16
                    }
                }
            }

            // Placeholder: Log
            Item {
                Rectangle {
                    anchors.centerIn: parent
                    color: "#1e1e2e"
                    radius: 12
                    width: 300; height: 100
                    Text {
                        anchors.centerIn: parent
                        text: "日志 — 输出（待实现）"
                        color: "#6c7086"
                        font.pixelSize: 16
                    }
                }
            }

            // Placeholder: Tools
            Item {
                Rectangle {
                    anchors.centerIn: parent
                    color: "#1e1e2e"
                    radius: 12
                    width: 300; height: 100
                    Text {
                        anchors.centerIn: parent
                        text: "工具 — 小工具集（待实现）"
                        color: "#6c7086"
                        font.pixelSize: 16
                    }
                }
            }

            // Settings page
            SettingsPage {
                id: settingsPage
            }

            // Placeholder: About
            Item {
                Rectangle {
                    anchors.centerIn: parent
                    color: "#1e1e2e"
                    radius: 12
                    width: 300; height: 100
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 8
                        Text {
                            text: "AVDC"
                            font.pixelSize: 24
                            font.bold: true
                            color: "#cdd6f4"
                            Layout.alignment: Qt.AlignHCenter
                        }
                        Text {
                            text: "PySide6 + QML 版"
                            font.pixelSize: 14
                            color: "#6c7086"
                            Layout.alignment: Qt.AlignHCenter
                        }
                    }
                }
            }
        }

        // Bottom tab bar
        TabBar {
            id: tabBar
            Layout.fillWidth: true
            background: Rectangle { color: "#1e1e2e" }

            TabButton { text: "主页"; width: implicitWidth + 16 }
            TabButton { text: "日志"; width: implicitWidth + 16 }
            TabButton { text: "工具"; width: implicitWidth + 16 }
            TabButton { text: "设置"; width: implicitWidth + 16 }
            TabButton { text: "关于"; width: implicitWidth + 16 }
        }
    }
}
