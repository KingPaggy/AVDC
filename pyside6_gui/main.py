#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AVDC PySide6 + QML GUI entry point."""
import sys
import os

# Ensure project root is on sys.path so `core` (avdc-core) imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtCore import QObject, Property, Qt, Signal, Slot
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow
from PySide6.QtWidgets import QApplication, QStyle

from settings_model import SettingsModel


class IconProvider(QQuickImageProvider):
    """Serve QStyle standard icons as images for QML."""

    def __init__(self, app):
        super().__init__(QQuickImageProvider.Image)
        self._app = app
        self._style_map = {
            "house": QStyle.SP_DirHomeIcon,
            "doc": QStyle.SP_FileIcon,
            "wrench": QStyle.SP_DialogApplyButton,
            "gear": QStyle.SP_DialogHelpButton,
            "info": QStyle.SP_MessageBoxInformation,
            "expand": QStyle.SP_ArrowRight,
            "collapse": QStyle.SP_ArrowLeft,
        }

    def requestImage(self, id, size, requestedSize):
        import re
        m = re.match(r"^(house|doc|wrench|gear|info|expand|collapse)", id)
        if not m:
            return QImage()
        sp = self._style_map.get(m.group(1))
        if sp is None:
            return QImage()
        style = self._app.style()
        icon = style.standardIcon(QStyle.StandardPixmap(sp))
        w = requestedSize.width() if requestedSize is not None else 16
        h = requestedSize.height() if requestedSize is not None else 16
        px = icon.pixmap(w, h)
        if size is not None:
            size.setWidth(px.width())
            size.setHeight(px.height())
        return px.toImage()


# Theme constants — exposed to QML as context property "Theme"
# Apple HIG 平台无关主题：语义化颜色（默认 Dark Mode）、8pt 网格间距、字号层级

# ===== 颜色（Apple HIG Dark Mode） =====
THEME = {
    # 文字颜色
    "textColor":      "#F5F5F7",
    "secondaryText":  "#98989D",
    "tertiaryText":   "#747476",
    # 语义颜色
    "accentColor":    "#0A84FF",
    "errorColor":     "#FF453A",
    "successColor":   "#30D158",
    "warningColor":   "#FF9F0A",
    "infoColor":      "#64D2FF",
    "purpleColor":    "#BF5AF2",
    "pinkColor":      "#FF375F",
    "mintColor":      "#66E0D8",
    "indigoColor":    "#5E5CE6",
    "yellowColor":    "#FFD60A",
    "brownColor":     "#AC8E68",
    # 背景颜色
    "backgroundColor": "#1E1E1E",
    "sidebarBg":      "#2D2D2D",
    "cardBg":         "#2D2D2D",
    "inputBg":        "#3A3A3C",
    "separatorColor": "#424245",
    # 交互颜色
    "hoverBg":        "#3A3A3C",
    "pressedBg":      "#48484A",
    "focusBorder":    "#0A84FF",
    # 间距（8pt 网格）
    "spacingXS":  4,
    "spacingSM":  8,
    "spacingMD":  12,
    "spacingLG":  16,
    "spacingXL":  20,
    "spacingXXL": 24,
    "spacingXXXL": 32,
    # 圆角
    "radiusXS": 2,
    "radiusSM": 4,
    "radiusMD": 6,
    "radiusLG": 8,
    "radiusXL": 12,
    # 字号层级
    "fontTitle":        16,
    "fontHeading":      13,
    "fontBody":         13,
    "fontCaption":      11,
    "fontMini":         10,
    "fontSidebarHeader": 12,
    "fontStat":         28,
    "fontLargeTitle":   34,
    "fontPageTitle":    28,
    # 侧边栏宽度
    "sidebarMin":   200,
    "sidebarIdeal": 240,
    "sidebarMax":   320,
    "sidebarIconOnly": 48,
    # 窗口规格
    "windowDefaultWidth": 1000,
    "windowDefaultHeight": 700,
    "windowMinWidth": 700,
    "windowMinHeight": 500,
    # 响应式断点
    "breakpointCompact": 600,
    "breakpointStandard": 900,
    # 动画时长
    "animationFast": 150,
    "animationNormal": 300,
    "animationSlow": 500,
    # 组件尺寸
    "titleBarHeight": 38,
    "titleBarButtonWidth": 36,
    "titleBarButtonHeight": 26,
    "navItemHeight": 32,
    "navItemSpacing": 2,
    "toastHeight": 40,
    "iconSize": 16,
    "indicatorWidth": 3,
    "labelWidthWide": 120,
    "labelWidthNarrow": 100,
    "logFilterBarHeight": 44,
    "progressBarHeight": 8,
    "resizeHandleSize": 8,
    # Toast 时长
    "toastDuration": 2000,
    "toastErrorDuration": 3000,
    # 页面布局
    "maxContentWidth": 680,
    "contentWidthPadding": 40,   # spacingXL * 2, used in Math.min(parent.width - contentWidthPadding, maxContentWidth)
    # About 页面
    "aboutCardWidth": 400,
    "aboutCardHeight": 320,
    "aboutDividerWidth": 300,
    # 字体
    "fontMonospace": "SF Mono, Menlo, Monaco, Courier New, monospace",
}


def main():
    # Use Basic style so we can customize TextField background, RadioButton, etc.
    os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"

    app = QApplication(sys.argv)
    app.setOrganizationName("AVDC")
    app.setApplicationName("AVDC-QML")

    # Create QML engine
    engine = QQmlApplicationEngine()

    # Register icon provider for QML
    icon_provider = IconProvider(app)
    engine.addImageProvider("styleicons", icon_provider)

    # Load settings model (exposed to QML as "settings")
    settings = SettingsModel()
    engine.rootContext().setContextProperty("settings", settings)
    engine.rootContext().setContextProperty("Theme", THEME)

    # WindowController must be registered BEFORE load() so QML can reference it
    class WindowController(QObject):
        """Bridge for QML to control the frameless window."""

        isMaximizedChanged = Signal()

        def __init__(self):
            super().__init__()
            self._win = None

        def set_window(self, win: QQuickWindow):
            self._win = win
            self._win.visibilityChanged.connect(self._on_visibility_changed)

        def _on_visibility_changed(self):
            self.isMaximizedChanged.emit()

        @Slot()
        def startMove(self):
            if self._win:
                self._win.startSystemMove()

        @Slot(int)
        def startResize(self, edge: int):
            if self._win:
                self._win.startSystemResize(Qt.Edge(edge))

        @Slot()
        def minimize(self):
            if self._win:
                self._win.showMinimized()

        @Slot()
        def maximize(self):
            if self._win:
                if self._win.visibility() == QQuickWindow.Maximized:
                    self._win.showNormal()
                else:
                    self._win.showMaximized()

        @Slot()
        def close(self):
            if self._win:
                self._win.close()

        @Property(bool, notify=isMaximizedChanged)
        def isMaximized(self):
            if self._win:
                return self._win.visibility() == QQuickWindow.Maximized
            return False

    controller = WindowController()
    engine.rootContext().setContextProperty("windowController", controller)

    # Load main QML
    qml_file = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print(f"Failed to load QML: {qml_file}")
        sys.exit(-1)

    # Make window frameless and wire up WindowController
    window = engine.rootObjects()[0]
    if isinstance(window, QQuickWindow):
        window.setFlags(
            Qt.FramelessWindowHint
            | Qt.WindowSystemMenuHint
            | Qt.WindowMinMaxButtonsHint
        )
        # Enable per-pixel alpha so QML transparent corners render smoothly
        window.setColor(Qt.transparent)
        controller.set_window(window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
