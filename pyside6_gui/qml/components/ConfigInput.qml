import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigInput — Label + TextField for string config values
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property string textValue: ""

    onTextValueChanged: {
        if (input.text !== textValue) input.text = textValue
    }

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.preferredWidth: 120
    }

    TextField {
        id: input
        text: root.textValue
        color: Theme.textColor
        font.pixelSize: Theme.fontBody
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
}
