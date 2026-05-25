import QtQuick 2.15
import QtQuick.Layouts 2.15
import AVDC 1.0

// AboutPage — version info, dependencies, credits
Item {
    id: aboutPage

    Rectangle {
        anchors.centerIn: parent
        color: Theme.cardBg
        radius: Theme.radiusXL
        width: 400
        height: 320

        ColumnLayout {
            anchors.centerIn: parent
            spacing: Theme.spacingSM

            // Title
            Text {
                text: "AVDC"
                font.pixelSize: Theme.fontPageTitle
                font.bold: true
                color: Theme.textColor
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "PySide6 + QML 版"
                font.pixelSize: Theme.fontBody
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 300
                implicitHeight: 1
                color: Theme.separatorColor
            }

            // Info
            Text {
                text: "版本: 0.1.0"
                font.pixelSize: Theme.fontBody
                color: Theme.secondaryText
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Python 3.13"
                font.pixelSize: Theme.fontCaption
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Apple HIG 设计规范"
                font.pixelSize: Theme.fontCaption
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 300
                implicitHeight: 1
                color: Theme.separatorColor
            }

            // Tech stack
            Text {
                text: "PySide6 · QML 2.15 · avdc-core"
                font.pixelSize: Theme.fontMini
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
