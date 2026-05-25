import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// SectionCard — 分组容器，带标题和分割线
Rectangle {
    id: root
    radius: Theme.radiusLG
    color: Theme.cardBg
    Layout.fillWidth: true
    implicitHeight: column.implicitHeight + Theme.spacingMD * 2

    property string sectionTitle: "Section"

    ColumnLayout {
        id: column
        anchors.fill: parent
        anchors.margins: Theme.spacingMD
        spacing: Theme.spacingSM

        Text {
            text: root.sectionTitle
            font.pixelSize: Theme.fontHeading
            font.bold: true
            color: Theme.textColor
            Layout.fillWidth: true
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.separatorColor
        }

    }
}
