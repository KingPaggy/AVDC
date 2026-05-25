import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigRadioGroup — Label + horizontal radio buttons
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property var options: []          // [{value: int|string, text: string}, ...]
    property var selectedValue: null  // current selected value

    Component.onCompleted: {
        if (options.length > 0 && selectedValue === null && options[0] !== undefined)
            selectedValue = options[0].value
    }

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.preferredWidth: Theme.labelWidthWide
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Theme.spacingLG
        Repeater {
            model: root.options
            RadioButton {
                text: modelData.text
                checked: modelData.value === root.selectedValue
                palette.buttonText: Theme.textColor
                palette.windowText: Theme.textColor
                onToggled: {
                    if (checked) root.selectedValue = modelData.value
                }
            }
        }
    }
}
