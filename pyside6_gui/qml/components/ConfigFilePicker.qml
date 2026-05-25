import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1 as LabPlatform
import AVDC 1.0

// ConfigFilePicker — Label + TextField + Browse button for directory paths
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingXS

    property string labelText: ""
    property string textValue: ""

    onTextValueChanged: {
        if (input.text !== textValue) input.text = textValue
    }

    signal folderSelected(string path)

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.preferredWidth: 100
    }

    TextField {
        id: input
        text: root.textValue
        color: Theme.textColor
        font.pixelSize: Theme.fontCaption
        Layout.fillWidth: true
        background: Rectangle {
            radius: Theme.radiusMD
            color: Theme.inputBg
            border.color: input.activeFocus ? Theme.focusBorder : Theme.separatorColor
            border.width: 1
        }
        onTextChanged: {
            if (root.textValue !== text) root.textValue = text
        }
    }

    Button {
        text: "浏览..."
        font.pixelSize: Theme.fontCaption
        onClicked: {
            folderDialog.open()
        }
    }

    LabPlatform.FolderDialog {
        id: folderDialog
        onAccepted: {
            root.textValue = folder.toString().replace("file://", "")
            root.folderSelected(root.textValue)
        }
    }
}
