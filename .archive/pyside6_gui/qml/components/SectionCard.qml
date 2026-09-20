import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// SectionCard — 分组容器，带标题、分割线和子内容区域
Rectangle {
    id: root
    radius: Theme.radiusLG
    color: Theme.cardBg
    width: parent.width

    property string sectionTitle: "Section"
    property string sectionDescription: ""
    default property alias contentData: contentColumn.children

    implicitHeight: contentColumn.implicitHeight + Theme.spacingMD * 2

    ColumnLayout {
        id: contentColumn
        width: parent.width - Theme.spacingMD * 2
        x: Theme.spacingMD
        y: Theme.spacingMD
        spacing: Theme.spacingSM

        Text {
            id: titleText
            text: root.sectionTitle
            font.family: Theme.fontFamilyDisplay
            font.pixelSize: Theme.fontTitle
            font.weight: Theme.weightSemibold
            color: Theme.textColor
            Layout.fillWidth: true
        }

        Text {
            id: descriptionText
            text: root.sectionDescription
            font.family: Theme.fontFamilySans
            font.pixelSize: Theme.fontCaption
            font.weight: Theme.weightRegular
            color: Theme.secondaryText
            lineHeight: Theme.lineHeightRelaxed
            lineHeightMode: Text.ProportionalHeight
            Layout.fillWidth: true
            visible: text !== ""
        }

        Rectangle {
            id: divider
            Layout.fillWidth: true
            implicitHeight: 1
            color: Theme.separatorColor
        }
    }

}
