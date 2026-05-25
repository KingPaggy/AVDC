import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import AVDC 1.0

// ConfigCheckbox — CheckBox with label for boolean config
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property bool checked: false

    onCheckedChanged: {
        if (cb.checked !== checked) cb.checked = checked
    }

    CheckBox {
        id: cb
        checked: root.checked
        palette.windowText: Theme.textColor
        onCheckedChanged: {
            if (root.checked !== checked) root.checked = checked
        }
    }

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.fillWidth: true
    }
}
