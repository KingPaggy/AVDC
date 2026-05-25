import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// StatusBadge — colored badge for success/error/warning/info states
Rectangle {
    id: root
    implicitHeight: 22
    implicitWidth: badgeText.implicitWidth + 16
    radius: 11
    color: _badgeColor

    property string status: "info"  // success | error | warning | info
    property string text: ""

    readonly property color _colorSuccess: "#a6e3a1"   // Green
    readonly property color _colorError: "#f38ba8"     // Red
    readonly property color _colorWarning: "#f9e2af"   // Yellow
    readonly property color _colorInfo: "#89dceb"      // Sky

    readonly property color _badgeColor: {
        switch (root.status) {
            case "success": return _colorSuccess
            case "error": return _colorError
            case "warning": return _colorWarning
            default: return _colorInfo
        }
    }

    Text {
        id: badgeText
        anchors.centerIn: parent
        text: root.text
        font.pixelSize: 12
        font.bold: true
        color: "#181825"  // Base
    }
}
