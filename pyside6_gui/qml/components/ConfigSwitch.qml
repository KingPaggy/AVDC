import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigSwitch — Label + Switch for boolean config values
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property bool checked: false
    property bool _suppressUpdate: false

    onCheckedChanged: {
        if (!_suppressUpdate && toggle.checked !== checked) {
            _suppressUpdate = true
            toggle.checked = checked
            _suppressUpdate = false
        }
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
