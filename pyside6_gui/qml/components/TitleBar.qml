import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15

// TitleBar — 自定义标题栏，用于无边框窗口
// 包含拖拽区域、标题文字、窗口控制按钮
Rectangle {
    id: root
    implicitHeight: 38
    color: Qt.darker(Theme.sidebarBg, 1.05)

    // 拖拽区域（最底层 z: 0，只覆盖空白区域）
    MouseArea {
        id: dragArea
        anchors.fill: parent
        anchors.rightMargin: buttonsRow.width + Theme.spacingSM

        property int pressGlobalX: 0
        property int pressGlobalY: 0
        property int windowX: 0
        property int windowY: 0

        onPressed: (mouse) => {
            var globalPos = dragArea.mapToGlobal(Qt.point(mouse.x, mouse.y))
            pressGlobalX = globalPos.x
            pressGlobalY = globalPos.y
            windowX = appWindow.x
            windowY = appWindow.y
        }

        onPositionChanged: (mouse) => {
            if (pressed) {
                var globalPos = dragArea.mapToGlobal(Qt.point(mouse.x, mouse.y))
                appWindow.x = windowX + (globalPos.x - pressGlobalX)
                appWindow.y = windowY + (globalPos.y - pressGlobalY)
            }
        }
    }

    // Title text (centered)
    Text {
        anchors.centerIn: parent
        anchors.leftMargin: 40  // make room for sidebar toggle
        font.pixelSize: Theme.fontBody
        font.bold: true
        color: Theme.textColor
        text: "AVDC"
    }

    // Sidebar toggle button (left side)
    TitleBarButton {
        anchors.left: parent.left
        anchors.leftMargin: Theme.spacingSM
        anchors.verticalCenter: parent.verticalCenter
        icon: appWindow.sidebarCollapsed ? "expand" : "collapse"
        buttonColor: Theme.accentColor
        onClicked: appWindow.sidebarCollapsed = !appWindow.sidebarCollapsed
    }

    // 窗口控制按钮行（覆盖在拖拽区域上方）
    Row {
        id: buttonsRow
        anchors.right: parent.right
        anchors.rightMargin: Theme.spacingSM
        anchors.verticalCenter: parent.verticalCenter
        spacing: Theme.spacingSM
        height: parent.height

        TitleBarButton {
            icon: "minus"
            buttonColor: Theme.successColor
            onClicked: windowController.minimize()
        }

        TitleBarButton {
            icon: windowController.isMaximized ? "restore" : "maximize"
            buttonColor: Theme.warningColor
            onClicked: windowController.maximize()
        }

        TitleBarButton {
            icon: "close"
            buttonColor: Theme.errorColor
            onClicked: windowController.close()
        }
    }
}
