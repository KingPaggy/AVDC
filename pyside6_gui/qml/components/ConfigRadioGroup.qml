import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigRadioGroup — Label + horizontal radio buttons
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: 12

    property string labelText: ""
    property var options: []          // [{value: int|string, text: string}, ...]
    property var selectedValue: null  // current selected value

    Component.onCompleted: {
        if (options.length > 0 && selectedValue === null)
            selectedValue = options[0].value
    }

    Text {
        text: root.labelText
        font.pixelSize: 14
        color: "#bac2de"
        Layout.preferredWidth: 120
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: 16
        Repeater {
            model: root.options
            RadioButton {
                text: modelData.text
                checked: modelData.value === root.selectedValue
                palette.buttonText: "#cdd6f4"
                palette.windowText: "#cdd6f4"
                onToggled: {
                    if (checked) root.selectedValue = modelData.value
                }
            }
        }
    }
}
