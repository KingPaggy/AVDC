import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.15

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
                implicitHeight: Theme.navItemHeight
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

                    // Icon (QStyle standard icons via image provider)
                    Image {
                        source: "image://styleIcons/" + modelData.icon
                        sourceSize.width: Theme.iconSize
                        sourceSize.height: Theme.iconSize
                        Layout.preferredWidth: Theme.iconSize
                        Layout.preferredHeight: Theme.iconSize
                        fillMode: Image.PreserveAspectFit
                        mipmap: true
                        opacity: root.currentIndex === index ? 1.0 : 0.7
                        Layout.leftMargin: Theme.spacingXS
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
    }
}
