import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

// ConfigSlider — Label + Slider + value display for numeric config
RowLayout {
    id: root
    Layout.fillWidth: true
    spacing: 12

    property string labelText: ""
    property int sliderValue: 0
    property int fromValue: 0
    property int toValue: 100

    onSliderValueChanged: {
        if (slider.value !== sliderValue) slider.value = sliderValue
    }

    Text {
        text: root.labelText
        font.pixelSize: 14
        color: "#bac2de"
        Layout.preferredWidth: 120
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
        font.pixelSize: 14
        font.bold: true
        color: "#89b4fa"
        Layout.preferredWidth: 30
        horizontalAlignment: Text.AlignRight
    }
}
