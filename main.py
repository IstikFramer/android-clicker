"""
LIFE OS 0.1 — точка входа.

Запуск:
    python main.py            # со splash-экраном
    python main.py --no-splash
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from lifeos import config as cfg
from lifeos.splash import SplashScreen
from lifeos.theme import DEFAULT_ACCENT, build_qss
from lifeos.window import MainWindow


def _pick_ui_font() -> QFont:
    families = set(QFontDatabase.families())
    for name in ("Inter", "Segoe UI Variable Display", "Segoe UI",
                 "SF Pro Display", "Noto Sans", "DejaVu Sans"):
        if name in families:
            f = QFont(name)
            f.setPointSize(10)
            f.setHintingPreference(QFont.PreferFullHinting)
            return f
    return QFont()


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(cfg.APP_NAME)
    app.setApplicationDisplayName(cfg.APP_NAME)
    app.setApplicationVersion(cfg.APP_VERSION)
    app.setOrganizationName(cfg.APP_ORG)
    app.setWindowIcon(QIcon(str(cfg.LOGO / "logo_256.png")))
    app.setQuitOnLastWindowClosed(False)  # живём в трее
    app.setFont(_pick_ui_font())
    app.setStyleSheet(build_qss(DEFAULT_ACCENT))

    window = MainWindow()

    if "--no-splash" in sys.argv:
        window.show()
    else:
        splash = SplashScreen(DEFAULT_ACCENT, duration_ms=2200)
        splash.finished.connect(window.show)
        splash.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
