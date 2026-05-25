import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ProgressBar — progress indicator with percentage and status text
Item {
    id: root
    Layout.fillWidth: true
    implicitHeight: 56

    property real progressValue: 0.0   // 0.0 - 1.0
    property string statusText: ""
    property bool showPercentage: true

    ColumnLayout {
        anchors.fill: parent
        spacing: 6

        // Bar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 8
            radius: 4
            color: "#313244"  // Surface0

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: parent.width * Math.min(Math.max(root.progressValue, 0), 1)
                radius: 4
                color: "#89b4fa"  // Blue
                Behavior on width {
                    NumberAnimation { duration: 150; easing.type: Easing.OutQuad }
                }
            }
        }

        // Status text + percentage
        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            Text {
                text: root.statusText
                font.pixelSize: 13
                color: "#bac2de"  // Subtext1
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            Text {
                visible: root.showPercentage
                text: Math.round(root.progressValue * 100) + "%"
                font.pixelSize: 12
                font.bold: true
                color: "#89b4fa"  // Blue
            }
        }
    }
}
