#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AVDC PySide6 + QML GUI entry point."""
import sys
import os

# Ensure project root is on sys.path so `core` (avdc-core) imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
from PySide6.QtCore import QObject, Property, Signal

from settings_model import SettingsModel


class Theme(QObject):
    """Apple HIG 平台无关主题单例 — Python 侧实现。"""

    # Signals for property change notification
    isDarkChanged = Signal()
    textColorChanged = Signal()
    accentColorChanged = Signal()
    errorColorChanged = Signal()
    successColorChanged = Signal()
    warningColorChanged = Signal()
    infoColorChanged = Signal()
    secondaryTextChanged = Signal()
    tertiaryTextChanged = Signal()
    purpleColorChanged = Signal()
    pinkColorChanged = Signal()
    mintColorChanged = Signal()
    indigoColorChanged = Signal()
    yellowColorChanged = Signal()
    brownColorChanged = Signal()
    backgroundColorChanged = Signal()
    sidebarBgChanged = Signal()
    cardBgChanged = Signal()
    inputBgChanged = Signal()
    separatorColorChanged = Signal()
    hoverBgChanged = Signal()
    pressedBgChanged = Signal()
    focusBorderColorChanged = Signal()

    # Dark Mode
    _is_dark = True  # Default to dark mode

    # ===== 文字颜色 =====
    @Property(str, notify=textColorChanged)
    def textColor(self):
        return "#F5F5F7" if self._is_dark else "#1D1D1F"

    @Property(str, notify=secondaryTextChanged)
    def secondaryText(self):
        return "#98989D" if self._is_dark else "#86868B"

    @Property(str, notify=tertiaryTextChanged)
    def tertiaryText(self):
        return "#747476" if self._is_dark else "#BFBFBF"

    # ===== 语义颜色 =====
    @Property(str, notify=accentColorChanged)
    def accentColor(self):
        return "#0A84FF" if self._is_dark else "#007AFF"

    @Property(str, notify=errorColorChanged)
    def errorColor(self):
        return "#FF453A" if self._is_dark else "#FF3B30"

    @Property(str, notify=successColorChanged)
    def successColor(self):
        return "#30D158" if self._is_dark else "#34C759"

    @Property(str, notify=warningColorChanged)
    def warningColor(self):
        return "#FF9F0A" if self._is_dark else "#FF9500"

    @Property(str, notify=infoColorChanged)
    def infoColor(self):
        return "#64D2FF" if self._is_dark else "#5AC8FA"

    @Property(str, notify=purpleColorChanged)
    def purpleColor(self):
        return "#BF5AF2" if self._is_dark else "#AF52DE"

    @Property(str, notify=pinkColorChanged)
    def pinkColor(self):
        return "#FF375F" if self._is_dark else "#FF2D55"

    @Property(str, notify=mintColorChanged)
    def mintColor(self):
        return "#66E0D8" if self._is_dark else "#00C7BE"

    @Property(str, notify=indigoColorChanged)
    def indigoColor(self):
        return "#5E5CE6" if self._is_dark else "#5856D6"

    @Property(str, notify=yellowColorChanged)
    def yellowColor(self):
        return "#FFD60A" if self._is_dark else "#FFCC00"

    @Property(str, notify=brownColorChanged)
    def brownColor(self):
        return "#AC8E68" if self._is_dark else "#A2845E"

    # ===== 背景颜色 =====
    @Property(str, notify=backgroundColorChanged)
    def backgroundColor(self):
        return "#1E1E1E" if self._is_dark else "#FFFFFF"

    @Property(str, notify=sidebarBgChanged)
    def sidebarBg(self):
        return "#2D2D2D" if self._is_dark else "#F5F5F7"

    @Property(str, notify=cardBgChanged)
    def cardBg(self):
        return "#2D2D2D" if self._is_dark else "#F5F5F7"

    @Property(str, notify=inputBgChanged)
    def inputBg(self):
        return "#3A3A3C" if self._is_dark else "#FFFFFF"

    @Property(str, notify=separatorColorChanged)
    def separatorColor(self):
        return "#424245" if self._is_dark else "#D1D1D6"

    # ===== 交互颜色 =====
    @Property(str, notify=hoverBgChanged)
    def hoverBg(self):
        return "#3A3A3C" if self._is_dark else "#E5E5EA"

    @Property(str, notify=pressedBgChanged)
    def pressedBg(self):
        return "#48484A" if self._is_dark else "#D1D1D6"

    @Property(str, notify=focusBorderColorChanged)
    def focusBorder(self):
        return self.accentColor

    # ===== 间距（8pt 网格） =====
    spacingXS = 4
    spacingSM = 8
    spacingMD = 12
    spacingLG = 16
    spacingXL = 20
    spacingXXL = 24
    spacingXXXL = 32

    # ===== 圆角 =====
    radiusSM = 4
    radiusMD = 6
    radiusLG = 8
    radiusXL = 12

    # ===== 字号层级 =====
    fontTitle = 16
    fontHeading = 13
    fontBody = 13
    fontCaption = 11
    fontMini = 10
    fontSidebarHeader = 12
    fontStat = 28
    fontLargeTitle = 34
    fontPageTitle = 28

    # ===== 侧边栏宽度 =====
    sidebarMin = 200
    sidebarIdeal = 240
    sidebarMax = 320
    sidebarIconOnly = 48

    # ===== 窗口规格 =====
    windowDefaultWidth = 1000
    windowDefaultHeight = 700
    windowMinWidth = 700
    windowMinHeight = 500

    # ===== 响应式断点 =====
    breakpointCompact = 600
    breakpointStandard = 900

    # ===== 动画时长 =====
    animationFast = 150
    animationNormal = 300
    animationSlow = 500


def _theme_singleton_provider(engine):
    return Theme()


def main():
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("AVDC")
    app.setApplicationName("AVDC-QML")

    # Load settings model (exposed to QML as "settings")
    settings = SettingsModel()

    # Create QML engine
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("settings", settings)

    # Register Theme as QML singleton (Python-based, accessible as "Theme" in QML)
    qmlRegisterSingletonType("AVDC", 1, 0, "Theme", _theme_singleton_provider)

    # Load main QML
    qml_file = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print(f"Failed to load QML: {qml_file}")
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
