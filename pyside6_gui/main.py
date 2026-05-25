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
from PySide6.QtQml import QQmlApplicationEngine

from settings_model import SettingsModel


def main():
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("AVDC")
    app.setApplicationName("AVDC-QML")

    # Load settings model (exposed to QML as "settings")
    settings = SettingsModel()

    # Create QML engine
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("settings", settings)

    # Register QML module path (for "import AVDC 1.0" — Theme singleton)
    qml_dir = os.path.join(os.path.dirname(__file__), "qml")
    engine.addImportPath(qml_dir)

    # Load main QML
    qml_file = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine.load(qml_file)

    if not engine.rootObjects():
        print(f"Failed to load QML: {qml_file}")
        sys.exit(-1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
