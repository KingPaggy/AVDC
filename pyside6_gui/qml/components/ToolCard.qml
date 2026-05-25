import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ToolCard — clickable card for tool items with title, description, and action
Rectangle {
    id: root
    Layout.fillWidth: true
    implicitHeight: 100
    radius: 8
    color: mouseArea.containsMouse ? "#313244" : "#1e1e2e"  // Surface0 on hover, Mantle default
    border.color: mouseArea.containsMouse ? "#89b4fa" : "#45475a"  // Blue on hover, Surface1 default
    border.width: 1

    property string title: ""
    property string description: ""
    property string actionLabel: "打开"

    signal clicked

    Behavior on color {
        ColorAnimation { duration: 150 }
    }
    Behavior on border.color {
        ColorAnimation { duration: 150 }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        spacing: 6

        Text {
            text: root.title
            font.pixelSize: 14
            font.bold: true
            color: "#cdd6f4"  // Text
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Text {
            text: root.description
            font.pixelSize: 13
            color: "#bac2de"  // Subtext1
            Layout.fillWidth: true
            elide: Text.ElideRight
            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
            maximumLineCount: 2
        }

        Item { Layout.fillHeight: true }

        Text {
            text: root.actionLabel + " →"
            font.pixelSize: 13
            font.bold: true
            color: mouseArea.containsMouse ? "#89b4fa" : "#6c7086"  // Blue on hover, Overlay2 default
            Behavior on color { ColorAnimation { duration: 150 } }
        }
    }
}
