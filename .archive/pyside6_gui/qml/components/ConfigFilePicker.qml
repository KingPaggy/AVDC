import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import Qt.labs.platform 1.1 as LabPlatform

// ConfigFilePicker — Label + TextField + Browse button for directory paths
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingXS

    property string labelText: ""
    property string textValue: ""
    property bool _suppressUpdate: false

    onTextValueChanged: {
        if (!_suppressUpdate && input.text !== textValue) {
            _suppressUpdate = true
            input.text = textValue
            _suppressUpdate = false
        }
    }

    Text {
        text: root.labelText
        font.family: Theme.fontFamilySans
        font.pixelSize: Theme.fontBody
        font.weight: Theme.weightRegular
        color: Theme.secondaryText
        Layout.preferredWidth: Theme.labelWidthWide
    }

    TextField {
        id: input
        text: root.textValue
        color: Theme.textColor
        font.family: Theme.fontFamilySans
        font.pixelSize: Theme.fontCaption
        font.weight: Theme.weightRegular
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
        font.family: Theme.fontFamilySans
        font.pixelSize: Theme.fontCaption
        font.weight: Theme.weightRegular
        onClicked: {
            folderDialog.open()
        }
    }

    LabPlatform.FolderDialog {
        id: folderDialog
        onAccepted: {
            root.textValue = folder.toString().replace("file://", "")
        }
    }
}
