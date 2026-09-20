import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ToolCard — clickable card for tool items with title, description, and action
Rectangle {
    id: root
    Layout.fillWidth: true
    implicitHeight: 100
    radius: Theme.radiusLG
    color: mouseArea.containsMouse ? Theme.hoverBg : Theme.cardBg
    border.color: mouseArea.containsMouse ? Theme.accentColor : Theme.separatorColor
    border.width: 1

    property string title: ""
    property string description: ""
    property string actionLabel: "打开"

    signal clicked

    Behavior on color {
        ColorAnimation { duration: Theme.animationFast }
    }
    Behavior on border.color {
        ColorAnimation { duration: Theme.animationFast }
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    Accessible.role: Accessible.Button
    Accessible.name: root.title
    Accessible.description: root.description

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingMD
        spacing: Theme.spacingXS

        Text {
            text: root.title
            font.family: Theme.fontFamilySans
            font.pixelSize: Theme.fontBody
            font.weight: Theme.weightSemibold
            color: Theme.textColor
            Layout.fillWidth: true
            elide: Text.ElideRight
        }

        Text {
            text: root.description
            font.family: Theme.fontFamilySans
            font.pixelSize: Theme.fontCaption
            font.weight: Theme.weightRegular
            color: Theme.secondaryText
            Layout.fillWidth: true
            elide: Text.ElideRight
            wrapMode: Text.WrapAtWordBoundaryOrAnywhere
            maximumLineCount: 2
        }

        Item { Layout.fillHeight: true }

        Text {
            text: root.actionLabel + " →"
            font.family: Theme.fontFamilySans
            font.pixelSize: Theme.fontCaption
            font.weight: Theme.weightSemibold
            color: mouseArea.containsMouse ? Theme.accentColor : Theme.tertiaryText
            Behavior on color { ColorAnimation { duration: Theme.animationFast } }
        }
    }
}
