import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// SectionCard — collapsible settings group with title
Rectangle {
    id: root
    radius: 8
    color: "#1e1e2e"
    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + 32

    property string sectionTitle: "Section"

    ColumnLayout {
        id: column
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        Text {
            text: root.sectionTitle
            font.pixelSize: 16
            font.bold: true
            color: "#cdd6f4"
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: "#45475a"
        }

        Loader {
            id: contentLoader
            Layout.fillWidth: true
        }
    }
}
