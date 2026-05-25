import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// StatusBadge — colored badge for success/error/warning/info states
Rectangle {
    id: root
    implicitHeight: 22
    implicitWidth: badgeText.implicitWidth + Theme.spacingSM
    radius: Theme.radiusXL
    color: _badgeColor

    property string status: "info"  // success | error | warning | info
    property string text: ""

    readonly property color _badgeColor: {
        switch (root.status) {
            case "success": return Theme.successColor
            case "error": return Theme.errorColor
            case "warning": return Theme.warningColor
            default: return Theme.infoColor
        }
    }

    Text {
        id: badgeText
        anchors.centerIn: parent
        text: root.text
        font.pixelSize: Theme.fontCaption
        font.bold: true
        color: Theme.backgroundColor
    }
}
