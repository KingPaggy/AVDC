import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import AVDC 1.0

// ConfigSwitch — Label + Switch for boolean config values
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property bool checked: false

    onCheckedChanged: {
        if (toggle.checked !== checked) toggle.checked = checked
    }

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.fillWidth: true
    }

    Switch {
        id: toggle
        checked: root.checked
        onCheckedChanged: {
            if (root.checked !== checked) root.checked = checked
        }
    }
}
