import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15
import AVDC 1.0

// MacOSSidebar — Apple HIG 风格侧边栏
// 宽度理想 240pt，可拖拽调整（200-320pt），支持折叠
Item {
    id: root
    implicitWidth: Theme.sidebarIdeal
    implicitHeight: 400

    property int currentIndex: 0
    property alias sidebarWidth: root.implicitWidth
    property bool collapsed: false

    signal itemClicked(int index)

    readonly property var navItems: [
        { icon: "house.fill",          label: "主页" },
        { icon: "doc.text.fill",       label: "日志" },
        { icon: "wrench.and.screwdriver.fill", label: "工具" },
        { icon: "gearshape.fill",      label: "设置" },
        { icon: "info.circle.fill",    label: "关于" }
    ]

    // Background with sidebar color
    Rectangle {
        id: bg
        anchors.fill: parent
        color: Theme.sidebarBg
    }

    // Separator line on the right edge
    Rectangle {
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 1
        color: Theme.separatorColor
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Theme.spacingSM
        spacing: 2

        // Section header
        Text {
            text: "导航"
            font.pixelSize: Theme.fontSidebarHeader
            font.bold: true
            color: Theme.tertiaryText
            Layout.fillWidth: true
            Layout.leftMargin: Theme.spacingXS
            Layout.topMargin: Theme.spacingXS
            Layout.bottomMargin: Theme.spacingXS
            visible: !root.collapsed
        }

        // Navigation items
        Repeater {
            model: root.navItems

            Rectangle {
                id: navItem
                Layout.fillWidth: true
                implicitHeight: 32
                radius: Theme.radiusSM
                color: mouseArea.containsMouse ? Theme.hoverBg : "transparent"
                visible: !root.collapsed

                Behavior on color {
                    ColorAnimation { duration: Theme.animationFast }
                }

                // Selected indicator
                Rectangle {
                    visible: root.currentIndex === index
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    anchors.margins: 4
                    width: 3
                    radius: 1.5
                    color: Theme.accentColor
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: Theme.spacingSM
                    anchors.rightMargin: Theme.spacingSM
                    spacing: Theme.spacingXS

                    // Icon placeholder (text-based until SF Symbols integration)
                    Text {
                        text: modelData.icon
                        font.pixelSize: 14
                        color: root.currentIndex === index ? Theme.accentColor : Theme.textColor
                        Layout.preferredWidth: 16
                        horizontalAlignment: Text.AlignHCenter
                    }

                    // Label
                    Text {
                        text: modelData.label
                        font.pixelSize: Theme.fontBody
                        color: root.currentIndex === index ? Theme.accentColor : Theme.textColor
                        Layout.fillWidth: true
                        elide: Text.ElideRight
                    }
                }

                MouseArea {
                    id: mouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        root.currentIndex = index
                        root.itemClicked(index)
                    }
                }
            }
        }

        Item { Layout.fillHeight: true }

        // Collapse/Expand toggle
        Button {
            text: root.collapsed ? "展开" : "折叠"
            font.pixelSize: Theme.fontCaption
            flat: true
            visible: !root.collapsed
            Layout.fillWidth: true
            Layout.bottomMargin: Theme.spacingXS
            palette.buttonText: Theme.tertiaryText
            onClicked: root.collapsed = true
        }
    }
}
