"""Оффскрин-рендер экранов LIFE OS в JPG (для превью и проверки вёрстки)."""
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
from lifeos.eula import EulaWindow  # noqa: E402
from lifeos.settings import settings  # noqa: E402
from lifeos.splash import SplashScreen  # noqa: E402
from lifeos.theme import build_qss  # noqa: E402
from lifeos.window import MainWindow  # noqa: E402

OUT = ROOT / "docs" / "preview"
OUT.mkdir(parents=True, exist_ok=True)


def wait(ms: int):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


def main():
    app = QApplication(sys.argv)
    settings.set("eula_accepted", True, save=False)
    app.setStyleSheet(build_qss())
    app.setWindowIcon(QIcon(str(cfg.LOGO / "logo_256.png")))

    w = MainWindow()
    w.resize(1440, 900)
    w.show()
    wait(900)

    for i, name in enumerate(["home", "settings", "about"]):
        w.go(i)
        wait(800)
        w.grab().save(str(OUT / f"{name}.jpg"), quality=90)
        print("saved", name)

    from lifeos.update_ui import UpdateWindow
    from lifeos.updater import UpdateInfo
    import json
    vj = json.loads((cfg.DATA / "version.json").read_text("utf-8"))
    info = UpdateInfo(version="0.3", title=vj["title"], notes="",
                      changes=vj["changes"], url=vj["url"], page=vj["page"],
                      size=41_500_000, published="2026-09-15",
                      source="branch", available=True)
    u = UpdateWindow(info)
    u.show(); wait(700)
    u.grab().save(str(OUT / "update.jpg"), quality=90); print("saved update")
    u._start(); wait(900)
    u.grab().save(str(OUT / "update_progress.jpg"), quality=90); print("saved update_progress")
    u._worker.cancel(); wait(400); u.close()

    e = EulaWindow(first_run=True)
    e.resize(880, 680)
    e.show()
    wait(700)
    e.grab().save(str(OUT / "eula.jpg"), quality=90)
    print("saved eula")
    e.close()

    s = SplashScreen(duration_s=6.0)
    s.show()
    wait(1600)
    s.grab().save(str(OUT / "splash.jpg"), quality=90)
    print("saved splash")
    s.close()


if __name__ == "__main__":
    main()
