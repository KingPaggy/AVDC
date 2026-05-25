import QtQuick 2.15
import QtQuick.Layouts 2.15

// AboutPage — version info, dependencies, credits
Item {
    id: aboutPage

    Rectangle {
        anchors.centerIn: parent
        color: "#1e1e2e"  // Mantle
        radius: 12
        width: 400
        height: 320

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 8

            // Title
            Text {
                text: "AVDC"
                font.pixelSize: 32
                font.bold: true
                color: "#cdd6f4"  // Text
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "PySide6 + QML 版"
                font.pixelSize: 14
                color: "#6c7086"  // Overlay2
                Layout.alignment: Qt.AlignHCenter
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 300
                implicitHeight: 1
                color: "#45475a"  // Surface1
            }

            // Info
            Text {
                text: "版本: 0.1.0"
                font.pixelSize: 14
                color: "#bac2de"  // Subtext1
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Python 3.13"
                font.pixelSize: 13
                color: "#6c7086"  // Overlay2
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Catppuccin Mocha 主题"
                font.pixelSize: 13
                color: "#6c7086"  // Overlay2
                Layout.alignment: Qt.AlignHCenter
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: 300
                implicitHeight: 1
                color: "#45475a"  // Surface1
            }

            // Tech stack
            Text {
                text: "PySide6 · QML 2.15 · avdc-core"
                font.pixelSize: 12
                color: "#6c7086"  // Overlay2
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
