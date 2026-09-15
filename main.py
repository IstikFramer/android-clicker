"""
LIFE OS — точка входа.

    python main.py              обычный запуск
    python main.py --no-splash  пропустить экран загрузки
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtWidgets import QApplication

from lifeos import config as cfg
from lifeos.anim import driver
from lifeos.settings import settings
from lifeos.splash import SplashScreen
from lifeos.theme import build_qss
from lifeos.window import MainWindow


def _ui_font() -> QFont:
    families = set(QFontDatabase.families())
    for name in ("Inter", "Segoe UI Variable Text", "Segoe UI",
                 "SF Pro Text", "Noto Sans", "DejaVu Sans"):
        if name in families:
            f = QFont(name)
            f.setPointSize(10)
            f.setHintingPreference(QFont.PreferFullHinting)
            return f
    return QFont()


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(cfg.APP_NAME)
    app.setApplicationDisplayName(cfg.APP_NAME)
    app.setApplicationVersion(cfg.APP_VERSION)
    app.setOrganizationName(cfg.DEV_NAME)
    app.setWindowIcon(QIcon(str(cfg.LOGO / "logo_256.png")))
    app.setQuitOnLastWindowClosed(False)
    app.setFont(_ui_font())
    app.setStyleSheet(build_qss())

    fps = settings.get("fps_limit")
    if settings.get("power_saving"):
        fps = min(fps, 30)
    driver().set_fps(fps)
    driver().set_speed(settings.speed)
    driver().set_enabled(settings.get("animations"))

    window = MainWindow()
    need_eula = not settings.get("eula_accepted")

    def open_app():
        if need_eula:
            window.show_eula(first_run=True)
        elif settings.get("start_minimized"):
            window.hide_to_tray()
        else:
            window.show()

    if "--no-splash" in sys.argv:
        open_app()
    else:
        splash = SplashScreen(duration_s=2.1)
        splash.finished.connect(open_app)
        splash.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
