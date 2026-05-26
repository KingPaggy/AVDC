import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import "components"

// AVDC 主窗口 — Apple HIG 无边框风格
// TitleBar + SplitView + 侧边栏 + Loader 按需加载页面 + 快捷键
ApplicationWindow {
    id: appWindow
    visible: true
    width: Theme.windowDefaultWidth
    height: Theme.windowDefaultHeight
    minimumWidth: Theme.windowMinWidth
    minimumHeight: Theme.windowMinHeight
    color: "transparent"

    // Sidebar state — exposed for TitleBar to access
    property bool sidebarCollapsed: false
    property bool sidebarExpandable: true
    property int resizeHandleSize: Theme.resizeHandleSize

    // 窗口圆角裁剪容器
    // 优化：背景 Rectangle 单独放置，内容区域用 clip + radius 替代 OpacityMask，避免 GPU 离屏渲染
    Rectangle {
        anchors.fill: parent
        color: Theme.backgroundColor
        radius: Theme.radiusXL
        clip: true
    }

    Item {
        id: roundedContainer
        anchors.fill: parent

        // ===== 自定义标题栏 =====
        TitleBar {
            id: titleBar
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            z: 20
        }

        // ===== SplitView 主布局（标题栏下方） =====
        SplitView {
            id: mainSplitView
            anchors.fill: parent
            anchors.topMargin: titleBar.height
            orientation: Qt.Horizontal

            // ===== 侧边栏 =====
            MacOSSidebar {
                id: sidebar
                collapsed: appWindow.sidebarCollapsed
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

            // ===== Content area =====
            Item {
                id: contentArea
                SplitView.fillWidth: true
                SplitView.fillHeight: true

                Component { id: homePageComponent; HomePage {} }
                Component { id: logPageComponent; LogPage {} }
                Component { id: toolsPageComponent; ToolsPage {} }
                Component { id: settingsPageComponent; SettingsPage {} }
                Component { id: aboutPageComponent; AboutPage {} }

                Loader {
                    id: pageLoader
                    anchors.fill: parent
                    property int currentPage: 0
                    property var _components: [homePageComponent, logPageComponent, toolsPageComponent, settingsPageComponent, aboutPageComponent]

                    onCurrentPageChanged: sourceComponent = _components[currentPage]

                    Component.onCompleted: sourceComponent = _components[0]
                }
            }
        }

        // ===== Toast 通知 =====
        Rectangle {
            id: toast
            anchors.horizontalCenter: parent.horizontalCenter
            y: -50
            width: Math.max(toastText.implicitWidth + Theme.spacingXL * 2, 160)
            height: Theme.toastHeight
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
                interval: Theme.toastDuration
                onTriggered: toast.y = -50
            }

            Timer {
                id: errorTimer
                interval: Theme.toastErrorDuration
                onTriggered: toast.y = -50
            }
        }

        // ===== 边缘调整大小区域 =====
        ResizeHandle { edge: Qt.TopEdge; x: resizeHandleSize; y: 0; width: parent.width - resizeHandleSize * 2; height: resizeHandleSize; z: 10 }
        ResizeHandle { edge: Qt.BottomEdge; x: resizeHandleSize; y: parent.height - resizeHandleSize; width: parent.width - resizeHandleSize * 2; height: resizeHandleSize; z: 10 }
        ResizeHandle { edge: Qt.LeftEdge; x: 0; y: resizeHandleSize; width: resizeHandleSize; height: parent.height - resizeHandleSize * 2; z: 10 }
        ResizeHandle { edge: Qt.RightEdge; x: parent.width - resizeHandleSize; y: resizeHandleSize; width: resizeHandleSize; height: parent.height - resizeHandleSize * 2; z: 10 }
    }

    // ===== Settings 事件连接 =====
    Connections {
        target: settings
        function onConfigSaved() { toast.show("配置已保存") }
        function onConfigLoaded() { toast.show("配置已加载") }
        function onErrorOccurred(msg: string) { toast.showError(msg) }
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
        onActivated: appWindow.sidebarCollapsed = !appWindow.sidebarCollapsed
    }
}
