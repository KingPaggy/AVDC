import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// SectionCard — 分组容器，带标题、分割线和子内容区域
Rectangle {
    id: root
    radius: Theme.radiusLG
    color: Theme.cardBg
    Layout.fillWidth: true
    implicitHeight: contentColumn.implicitHeight + Theme.spacingMD * 2

    property string sectionTitle: "Section"
    default property alias contentData: contentColumn.children

    Column {
        id: contentColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Theme.spacingMD
        spacing: Theme.spacingSM

        Text {
            text: root.sectionTitle
            font.pixelSize: Theme.fontHeading
            font.bold: true
            color: Theme.textColor
            width: parent.width
        }

        Rectangle {
            width: parent.width
            implicitHeight: 1
            color: Theme.separatorColor
        }
    }
}
