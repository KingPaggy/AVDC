import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import AVDC 1.0

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
        spacing: Theme.spacingSM

        // Bar
        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 8
            radius: Theme.radiusMD
            color: Theme.inputBg

            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: parent.width * Math.min(Math.max(root.progressValue, 0), 1)
                radius: Theme.radiusMD
                color: Theme.accentColor
                Behavior on width {
                    NumberAnimation { duration: Theme.animationFast; easing.type: Easing.OutQuad }
                }
            }
        }

        // Status text + percentage
        RowLayout {
            Layout.fillWidth: true
            spacing: Theme.spacingSM

            Text {
                text: root.statusText
                font.pixelSize: Theme.fontCaption
                color: Theme.secondaryText
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            Text {
                visible: root.showPercentage
                text: Math.round(root.progressValue * 100) + "%"
                font.pixelSize: Theme.fontCaption
                font.bold: true
                color: Theme.accentColor
            }
        }
    }
}
