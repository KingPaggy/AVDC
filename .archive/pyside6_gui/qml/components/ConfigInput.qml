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
    property bool _suppressUpdate: false

    // Sync external textValue change to input field
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
        font.pixelSize: Theme.fontBody
        font.weight: Theme.weightRegular
        Layout.fillWidth: true
        background: Rectangle {
            radius: Theme.radiusMD
            color: Theme.inputBg
            border.color: input.activeFocus ? Theme.focusBorder : Theme.separatorColor
            border.width: 1
        }
        // Sync user input back to textValue
        onTextChanged: {
            if (!root._suppressUpdate && root.textValue !== text) {
                root.textValue = text
            }
        }
    }
}
