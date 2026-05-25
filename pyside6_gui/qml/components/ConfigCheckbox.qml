import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigCheckbox — CheckBox with label for boolean config
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: 12

    property string labelText: ""
    property bool checked: false

    onCheckedChanged: {
        if (cb.checked !== checked) cb.checked = checked
    }

    CheckBox {
        id: cb
        checked: root.checked
        palette.windowText: "#cdd6f4"
        onCheckedChanged: {
            if (root.checked !== checked) root.checked = checked
        }
    }

    Text {
        text: root.labelText
        font.pixelSize: 14
        color: "#bac2de"
        Layout.fillWidth: true
    }
}
