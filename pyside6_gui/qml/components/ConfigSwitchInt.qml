import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigSwitchInt — Label + Switch for int-based boolean config (0/1)
// Wraps ConfigSwitch to handle int <-> bool conversion internally
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property int intValue: 0
    property bool _suppressUpdate: false

    // Sync external intValue change to toggle
    onIntValueChanged: {
        if (!_suppressUpdate && toggle.checked !== (intValue === 1)) {
            _suppressUpdate = true
            toggle.checked = intValue === 1
            _suppressUpdate = false
        }
    }

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.preferredWidth: Theme.labelWidthWide
    }

    Switch {
        id: toggle
        checked: root.intValue === 1
        onCheckedChanged: {
            if (!root._suppressUpdate) {
                root._suppressUpdate = true
                root.intValue = checked ? 1 : 0
                root._suppressUpdate = false
            }
        }
    }
}
