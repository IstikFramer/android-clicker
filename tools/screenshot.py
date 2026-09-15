"""Оффскрин-рендер экранов LIFE OS в PNG (для превью и проверки вёрстки)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import QEventLoop, QTimer  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from lifeos import config as cfg  # noqa: E402
from lifeos.splash import SplashScreen  # noqa: E402
from lifeos.theme import DEFAULT_ACCENT, build_qss  # noqa: E402
from lifeos.window import MainWindow  # noqa: E402

OUT = ROOT / "docs" / "preview"
OUT.mkdir(parents=True, exist_ok=True)


def wait(ms: int):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(build_qss(DEFAULT_ACCENT))
    app.setWindowIcon(QIcon(str(cfg.LOGO / "logo_256.png")))

    w = MainWindow()
    w.resize(1440, 900)
    w.show()
    wait(900)

    names = ["dashboard", "tools", "settings", "about"]
    for i, name in enumerate(names):
        w.go(i)
        wait(700)
        w.grab().save(str(OUT / f"{name}.jpg"), quality=90)
        print("saved", name)

    s = SplashScreen(DEFAULT_ACCENT, duration_ms=1200)
    s.show()
    wait(700)
    s.grab().save(str(OUT / "splash.jpg"), quality=90)
    print("saved splash")
    s.close()


if __name__ == "__main__":
    main()
