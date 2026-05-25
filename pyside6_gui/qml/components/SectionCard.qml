import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// SectionCard — 分组容器，带标题、分割线和子内容区域
Rectangle {
    id: root
    radius: Theme.radiusLG
    color: Theme.cardBg
    Layout.fillWidth: true

    property string sectionTitle: "Section"
    default property alias contentData: column.children

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
