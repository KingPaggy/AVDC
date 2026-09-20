import QtQuick 2.15
import QtQuick.Controls 2.15

// TitleBarButton — 单个窗口控制按钮（最小化/最大化/关闭）
Rectangle {
    id: root
    implicitWidth: Theme.titleBarButtonWidth
    implicitHeight: Theme.titleBarButtonHeight
    radius: Theme.radiusSM
    color: mouseArea.containsMouse ? Qt.lighter(buttonColor, 1.3) : "transparent"
    border.color: mouseArea.containsMouse ? buttonColor : "transparent"
    border.width: 1

    property color buttonColor: Theme.accentColor
    property string icon: "close"

    Behavior on color {
        ColorAnimation { duration: Theme.animationFast }
    }

    Text {
        anchors.centerIn: parent
        text: {
            switch (root.icon) {
                case "minus": return "—"
                case "maximize": return "□"
                case "restore": return "⧉"
                case "close": return "×"
                case "expand": return "▶"
                case "collapse": return "◀"
                default: return ""
            }
        }
        font.family: Theme.fontFamilySans
        font.pixelSize: Theme.fontBody
        font.weight: Theme.weightSemibold
        color: mouseArea.containsMouse ? root.buttonColor : Theme.secondaryText
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    signal clicked()

    Accessible.role: Accessible.Button
    Accessible.name: {
        switch (root.icon) {
            case "close": return "关闭"
            case "minimize": return "最小化"
            case "maximize": return "最大化"
            case "restore": return "还原"
            case "expand": return "展开"
            case "collapse": return "折叠"
            default: return ""
        }
    }
}
