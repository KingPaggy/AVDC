import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigSlider — Label + Slider + value display for numeric config
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: Theme.spacingSM

    property string labelText: ""
    property int sliderValue: 0
    property int fromValue: 0
    property int toValue: 100
    property bool _suppressUpdate: false

    onSliderValueChanged: {
        if (!_suppressUpdate && slider.value !== sliderValue) {
            _suppressUpdate = true
            slider.value = sliderValue
            _suppressUpdate = false
        }
    }

    Text {
        text: root.labelText
        font.pixelSize: Theme.fontBody
        color: Theme.secondaryText
        Layout.preferredWidth: Theme.labelWidthWide
    }

    Slider {
        id: slider
        from: root.fromValue
        to: root.toValue
        value: root.sliderValue
        stepSize: 1
        Layout.fillWidth: true
        onValueChanged: {
            if (root.sliderValue !== Math.round(value))
                root.sliderValue = Math.round(value)
        }
    }

    Text {
        text: Math.round(slider.value).toString()
        font.pixelSize: Theme.fontCaption
        font.bold: true
        color: Theme.accentColor
        Layout.preferredWidth: 30
        horizontalAlignment: Text.AlignRight
    }
}
