"""LIFE OS — стартовый экран загрузки (безрамочный, с логотипом и прогрессом)."""
from __future__ import annotations

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPixmap,
)
from PySide6.QtWidgets import QWidget

from . import config as cfg
from .theme import ACCENTS, DEFAULT_ACCENT

STEPS = [
    "Инициализация ядра…",
    "Загрузка темы Dark Glass…",
    "Подготовка графики 4K…",
    "Сборка модулей оболочки…",
    "Подключение системного трея…",
    "Готово",
]


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self, accent_key: str = DEFAULT_ACCENT, duration_ms: int = 2200):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(620, 360)

        self._acc = ACCENTS[accent_key]
        self._bg = QPixmap(str(cfg.BACKGROUNDS / "splash.jpg")).scaled(
            self.size() * 1.0, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self._logo = QPixmap(str(cfg.LOGO / "logo_512.png")).scaled(
            132, 132, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self._progress = 0.0
        self._step = 0
        self._tick_ms = 16
        self._per_tick = 100.0 / max(1, duration_ms / self._tick_ms)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(self._tick_ms)
        self._center()

    def _center(self):
        scr = self.screen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2,
                  scr.center().y() - self.height() // 2)

    def _tick(self):
        self._progress = min(100.0, self._progress + self._per_tick)
        self._step = min(len(STEPS) - 1, int(self._progress / 100 * (len(STEPS) - 1) + 0.001))
        self.update()
        if self._progress >= 100.0:
            self._timer.stop()
            QTimer.singleShot(260, self._done)

    def _done(self):
        self.finished.emit()
        self.close()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), 20, 20)
        p.setClipPath(path)

        p.fillRect(r, QColor("#05070D"))
        if not self._bg.isNull():
            p.drawPixmap(
                int((r.width() - self._bg.width()) / 2),
                int((r.height() - self._bg.height()) / 2),
                self._bg,
            )
        veil = QLinearGradient(0, 0, 0, r.height())
        veil.setColorAt(0.0, QColor(5, 7, 13, 170))
        veil.setColorAt(1.0, QColor(5, 7, 13, 238))
        p.fillRect(r, QBrush(veil))

        if not self._logo.isNull():
            p.drawPixmap(int((r.width() - self._logo.width()) / 2), 52, self._logo)

        p.setPen(QColor("#EAF2FF"))
        f = QFont()
        f.setPointSize(19)
        f.setWeight(QFont.Black)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 6)
        p.setFont(f)
        p.drawText(QRectF(0, 198, r.width(), 30), Qt.AlignCenter, "LIFE OS")

        f2 = QFont()
        f2.setPointSize(8)
        f2.setWeight(QFont.DemiBold)
        f2.setLetterSpacing(QFont.AbsoluteSpacing, 2)
        p.setFont(f2)
        p.setPen(QColor(self._acc.primary))
        p.drawText(QRectF(0, 228, r.width(), 20), Qt.AlignCenter,
                   f"VERSION {cfg.APP_VERSION}  ·  {cfg.APP_TAGLINE.upper()}")

        # прогресс
        bar = QRectF(90, 286, r.width() - 180, 6)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 24))
        p.drawRoundedRect(bar, 3, 3)
        fill = QRectF(bar)
        fill.setWidth(bar.width() * self._progress / 100.0)
        g = QLinearGradient(fill.left(), 0, bar.right(), 0)
        g.setColorAt(0.0, QColor(self._acc.primary))
        g.setColorAt(1.0, QColor(self._acc.secondary))
        glow = QColor(self._acc.primary)
        glow.setAlpha(70)
        p.setBrush(glow)
        p.drawRoundedRect(fill.adjusted(-2, -3, 2, 3), 6, 6)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(fill, 3, 3)

        f3 = QFont()
        f3.setPointSize(8)
        p.setFont(f3)
        p.setPen(QColor("#6B7A94"))
        p.drawText(QRectF(90, 302, bar.width(), 22), Qt.AlignLeft | Qt.AlignVCenter,
                   STEPS[self._step])
        p.drawText(QRectF(90, 302, bar.width(), 22), Qt.AlignRight | Qt.AlignVCenter,
                   f"{int(self._progress)}%")

        p.setBrush(Qt.NoBrush)
        edge = QColor(self._acc.primary)
        edge.setAlpha(70)
        p.setPen(edge)
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 20, 20)
        p.end()
