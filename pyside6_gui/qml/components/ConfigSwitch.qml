import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigSwitch — Label + Switch for boolean config values
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: 12

    property string labelText: ""
    property bool checked: false

    onCheckedChanged: {
        if (toggle.checked !== checked) toggle.checked = checked
    }

    Text {
        text: root.labelText
        font.pixelSize: 14
        color: "#bac2de"
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
