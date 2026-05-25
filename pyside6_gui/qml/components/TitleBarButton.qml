import QtQuick 2.15
import QtQuick.Controls 2.15

// TitleBarButton — 单个窗口控制按钮（最小化/最大化/关闭）
Rectangle {
    id: root
    implicitWidth: 36
    implicitHeight: 26
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
                default: return ""
            }
        }
        font.pixelSize: 14
        font.bold: true
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
}
