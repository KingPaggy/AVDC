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
    default property alias contentData: contentColumn.children

    Column {
        id: contentColumn
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: Theme.spacingMD
        spacing: Theme.spacingSM

        Text {
            id: titleText
            text: root.sectionTitle
            font.pixelSize: Theme.fontHeading
            font.bold: true
            color: Theme.textColor
            width: parent.width
        }

        Rectangle {
            id: divider
            width: parent.width
            implicitHeight: 1
            color: Theme.separatorColor
        }
    }

    // implicitHeight: sum of all children heights + spacing + margins
    implicitHeight: {
        var h = Theme.spacingMD * 2  // top + bottom margin
        if (titleText.implicitHeight > 0) h += titleText.implicitHeight
        if (divider.implicitHeight > 0) h += divider.implicitHeight
        for (var i = 0; i < contentColumn.children.length; i++) {
            var c = contentColumn.children[i]
            var ch = c.implicitHeight || c.Layout.preferredHeight || 0
            if (ch > 0) h += ch
        }
        // spacing between items
        var n = 1 + 1 + contentColumn.children.length  // title + divider + children
        if (n > 1) h += contentColumn.spacing * (n - 1)
        return h
    }
}
