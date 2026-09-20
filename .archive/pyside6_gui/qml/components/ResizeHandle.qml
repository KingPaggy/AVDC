import QtQuick 2.15

// ResizeHandle — 无边框窗口边缘的拖拽调整大小区域
// Qt.Edge 只有 Top/Bottom/Left/Right 四个值，corner 通过相邻两边覆盖
MouseArea {
    id: root
    property int edge: Qt.TopEdge

    hoverEnabled: true
    onPositionChanged: {
        switch (edge) {
            case Qt.TopEdge:
            case Qt.BottomEdge:
                cursorShape = Qt.SizeVerCursor
                break
            case Qt.LeftEdge:
            case Qt.RightEdge:
                cursorShape = Qt.SizeHorCursor
                break
            case Qt.TopLeftEdge:
            case Qt.BottomRightEdge:
                cursorShape = Qt.SizeFDiagCursor
                break
            case Qt.TopRightEdge:
            case Qt.BottomLeftEdge:
                cursorShape = Qt.SizeBDiagCursor
                break
            default:
                cursorShape = Qt.ArrowCursor
        }
    }

    onPressed: {
        windowController.startResize(edge)
    }
}
