import QtQuick 2.15
import QtQuick.Layouts 2.15

// AboutPage — version info, dependencies, credits
Item {
    objectName: "aboutPage"
    id: aboutPage

    Rectangle {
        anchors.centerIn: parent
        color: Theme.cardBg
        radius: Theme.radiusXL
        width: Theme.aboutCardWidth
        height: Theme.aboutCardHeight

        ColumnLayout {
            anchors.centerIn: parent
            spacing: Theme.spacingSM

            // Title
            Text {
                text: "AVDC"
                font.family: Theme.fontFamilyDisplay
                font.pixelSize: Theme.fontPageTitle
                font.weight: Theme.weightBold
                color: Theme.textColor
                lineHeight: Theme.lineHeightTight
                lineHeightMode: Text.ProportionalHeight
                font.letterSpacing: Theme.letterSpacingTight
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "PySide6 + QML 版"
                font.family: Theme.fontFamilySans
                font.pixelSize: Theme.fontBody
                font.weight: Theme.weightRegular
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: Theme.aboutDividerWidth
                implicitHeight: 1
                color: Theme.separatorColor
            }

            // Info
            Text {
                text: "版本: 0.1.0"
                font.family: Theme.fontFamilySans
                font.pixelSize: Theme.fontBody
                font.weight: Theme.weightRegular
                color: Theme.secondaryText
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Python 3.13"
                font.family: Theme.fontFamilySans
                font.pixelSize: Theme.fontCaption
                font.weight: Theme.weightRegular
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }

            Text {
                text: "Apple HIG 设计规范"
                font.family: Theme.fontFamilySans
                font.pixelSize: Theme.fontCaption
                font.weight: Theme.weightRegular
                color: Theme.tertiaryText
                Layout.alignment: Qt.AlignHCenter
            }

            // Divider
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredWidth: Theme.aboutDividerWidth
                implicitHeight: 1
                color: Theme.separatorColor
            }

            // Tech stack
            Text {
                text: "PySide6 · QML 2.15 · avdc-core"
                font.family: Theme.fontFamilySans
                font.pixelSize: Theme.fontMini
                font.weight: Theme.weightRegular
                color: Theme.tertiaryText
                lineHeight: Theme.lineHeightRelaxed
                lineHeightMode: Text.ProportionalHeight
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}
