import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigInput — Label + TextField for string config values
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: 12

    property string labelText: ""
    property string textValue: ""

    onTextValueChanged: {
        if (input.text !== textValue) input.text = textValue
    }

    Text {
        text: root.labelText
        font.pixelSize: 14
        color: "#bac2de"
        Layout.preferredWidth: 120
    }

    TextField {
        id: input
        text: root.textValue
        color: "#cdd6f4"
        font.pixelSize: 14
        Layout.fillWidth: true
        background: Rectangle {
            radius: 6
            color: "#313244"
            border.color: input.activeFocus ? "#89b4fa" : "#45475a"
            border.width: 1
        }
        onTextChanged: {
            if (root.textValue !== text) root.textValue = text
        }
    }
}
