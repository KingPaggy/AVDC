import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// AVDC 主窗口 — Apple HIG 桌面架构
// SplitView + 侧边栏 + Loader 按需加载页面 + MenuBar + 快捷键
ApplicationWindow {
    id: appWindow
    visible: true
    width: Theme.windowDefaultWidth
    height: Theme.windowDefaultHeight
    minimumWidth: Theme.windowMinWidth
    minimumHeight: Theme.windowMinHeight
    title: "AVDC — PySide6 QML"
    color: Theme.backgroundColor

    // ===== MenuBar =====
    menuBar: MenuBar {
        Menu {
            title: "文件"
            MenuItem { text: "新建窗口\tCtrl+N"; onTriggered: toast.show("新建窗口（待实现）") }
            MenuItem { text: "打开...\tCtrl+O"; onTriggered: toast.show("打开文件（待实现）") }
            MenuSeparator {}
            MenuItem { text: "关闭窗口\tCtrl+W"; onTriggered: appWindow.close() }
        }
        Menu {
            title: "编辑"
            MenuItem { text: "撤销\tCtrl+Z"; onTriggered: toast.show("撤销（待实现）") }
            MenuItem { text: "重做\tCtrl+Shift+Z"; onTriggered: toast.show("重做（待实现）") }
            MenuSeparator {}
            MenuItem { text: "复制\tCtrl+C" }
            MenuItem { text: "粘贴\tCtrl+V" }
            MenuItem { text: "全选\tCtrl+A" }
        }
        Menu {
            title: "视图"
            MenuItem {
                text: sidebar.collapsed ? "显示侧边栏\tCtrl+Shift+S" : "隐藏侧边栏\tCtrl+Shift+S"
                onTriggered: sidebar.collapsed = !sidebar.collapsed
            }
        }
        Menu {
            title: "工具"
            MenuItem { text: "开始处理\tCtrl+Return"; onTriggered: toast.show("开始处理（待实现）") }
            MenuItem { text: "停止\tEsc"; onTriggered: toast.show("已停止（待实现）") }
        }
        Menu {
            title: "帮助"
            MenuItem { text: "关于 AVDC"; onTriggered: sidebar.currentIndex = 4 }
        }
    }

    // ===== Toast 通知 =====
    Rectangle {
        id: toast
        anchors.horizontalCenter: parent.horizontalCenter
        y: -50
        width: Math.max(toastText.implicitWidth + Theme.spacingXL * 2, 160)
        height: 40
        radius: Theme.radiusLG
        color: Theme.successColor
        z: 100
        Behavior on y {
            NumberAnimation { duration: Theme.animationNormal; easing.type: Easing.OutCubic }
        }

        Text {
            id: toastText
            anchors.centerIn: parent
            font.pixelSize: Theme.fontBody
            font.bold: true
            color: Theme.backgroundColor
        }

        function show(message: string) {
            toastText.text = message
            toast.color = Theme.successColor
            y = Theme.spacingXL
            timer.restart()
        }

        function showError(message: string) {
            toastText.text = message
            toast.color = Theme.errorColor
            y = Theme.spacingXL
            errorTimer.restart()
        }

        Timer {
            id: timer
            interval: 2000
            onTriggered: toast.y = -50
        }

        Timer {
            id: errorTimer
            interval: 3000
            onTriggered: toast.y = -50
        }
    }

    // ===== Settings 事件连接 =====
    Connections {
        target: settings
        function onConfigSaved() { toast.show("配置已保存") }
        function onConfigLoaded() { toast.show("配置已加载") }
        function onErrorOccurred(msg: string) { toast.showError(msg) }
    }

    // ===== SplitView 主布局 =====
    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        // ===== 侧边栏 =====
        MacOSSidebar {
            id: sidebar
            Layout.fillHeight: true
            Layout.minimumWidth: sidebar.collapsed ? 0 : Theme.sidebarMin
            Layout.preferredWidth: sidebar.collapsed ? 0 : Theme.sidebarIdeal
            Layout.maximumWidth: Theme.sidebarMax

            SplitView.minimumWidth: sidebar.collapsed ? 0 : Theme.sidebarMin
            SplitView.preferredWidth: sidebar.collapsed ? 0 : Theme.sidebarIdeal

            visible: !sidebar.collapsed

            onItemClicked: function(index) {
                pageLoader.currentPage = index
            }
        }

        // ===== 内容区域 =====
        Item {
            SplitView.fillWidth: true
            SplitView.fillHeight: true

            // Page loader with index-based switching
            Loader {
                id: pageLoader
                anchors.fill: parent

                property int currentPage: 0

                onCurrentPageChanged: {
                    switch (currentPage) {
                        case 0: source = "HomePage.qml"; break
                        case 1: source = "LogPage.qml"; break
                        case 2: source = "ToolsPage.qml"; break
                        case 3: source = "SettingsPage.qml"; break
                        case 4: source = "AboutPage.qml"; break
                        default: source = "HomePage.qml"
                    }
                }

                // Default page
                Component.onCompleted: currentPage = 0
            }
        }
    }

    // ===== 快捷键 =====
    Shortcut {
        sequences: [StandardKey.New]
        onActivated: toast.show("新建窗口（待实现）")
    }
    Shortcut {
        sequences: [StandardKey.Open]
        onActivated: toast.show("打开文件（待实现）")
    }
    Shortcut {
        sequences: [StandardKey.Close]
        onActivated: appWindow.close()
    }
    Shortcut {
        sequences: [StandardKey.Quit]
        onActivated: Qt.quit()
    }
    Shortcut {
        sequences: [StandardKey.Undo]
        onActivated: toast.show("撤销（待实现）")
    }
    Shortcut {
        sequences: [StandardKey.Redo]
        onActivated: toast.show("重做（待实现）")
    }
    Shortcut {
        sequences: [StandardKey.Save]
        onActivated: settings.save()
    }
    Shortcut {
        sequence: "Meta+,"
        onActivated: sidebar.currentIndex = 3
    }
    Shortcut {
        sequences: ["Meta+Shift+S", "Ctrl+Shift+S"]
        onActivated: sidebar.collapsed = !sidebar.collapsed
    }
}
