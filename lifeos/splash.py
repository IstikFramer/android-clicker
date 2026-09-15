"""LIFE OS — экран загрузки: орб, название, прогресс и этапы запуска."""
from __future__ import annotations

import math

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (
    QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import QWidget

from . import config as cfg
from .anim import Spring, driver, ease_out_cubic
from .theme import current_accent

STEPS = [
    (0.00, "Инициализация"),
    (0.18, "Загрузка оформления"),
    (0.40, "Подготовка графики"),
    (0.62, "Сборка интерфейса"),
    (0.84, "Почти готово"),
    (1.00, "Запуск"),
]


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self, duration_s: float = 2.1):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(640, 392)

        self._bg = QPixmap(str(cfg.BACKGROUNDS / "splash.jpg"))
        self._orb = QPixmap(str(cfg.LOGO / "logo_512.png")).scaled(
            146, 146, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self._t = 0.0
        self._duration = max(0.6, duration_s)
        self._progress = Spring(0.0, 9.0)
        self._fade = 0.0
        self._done = False
        self._phase = 0.0
        driver().subscribe(self, self._tick)
        self._center()

    def _center(self):
        scr = self.screen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2,
                  scr.center().y() - self.height() // 2)

    def _tick(self, dt: float):
        self._t += dt
        self._phase = (self._phase + dt * 1.6) % (math.pi * 2)
        self._fade = min(1.0, self._fade + dt * 3.2)
        self._progress.set(min(1.0, self._t / self._duration) * 100.0)
        self._progress.step(dt)
        self.update()
        if not self._done and self._t >= self._duration + 0.25:
            self._done = True
            driver().unsubscribe(self)
            QTimer.singleShot(120, self._finish)

    def _finish(self):
        self.finished.emit()
        self.close()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = self.rect()
        acc = current_accent()
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), 22, 22)
        p.setClipPath(path)
        p.setOpacity(ease_out_cubic(self._fade))

        p.fillRect(r, QColor("#04060C"))
        if not self._bg.isNull():
            scaled = self._bg.scaled(r.size(), Qt.KeepAspectRatioByExpanding,
                                     Qt.SmoothTransformation)
            p.drawPixmap(int((r.width() - scaled.width()) / 2),
                         int((r.height() - scaled.height()) / 2), scaled)
        veil = QLinearGradient(0, 0, 0, r.height())
        veil.setColorAt(0.0, QColor(4, 6, 12, 150))
        veil.setColorAt(1.0, QColor(4, 6, 12, 240))
        p.fillRect(r, QBrush(veil))

        # орб с дыханием
        pulse = 0.5 + 0.5 * math.sin(self._phase)
        cx, cy = r.width() / 2, 124.0
        halo = QRadialGradient(cx, cy, 116 + 8 * pulse)
        c = QColor(acc.primary)
        c.setAlphaF(0.20 + 0.08 * pulse)
        halo.setColorAt(0.0, c)
        c0 = QColor(acc.primary)
        c0.setAlpha(0)
        halo.setColorAt(1.0, c0)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(halo))
        p.drawEllipse(QRectF(cx - 130, cy - 130, 260, 260))

        if not self._orb.isNull():
            sc = 1.0 + 0.018 * pulse
            w = self._orb.width() * sc
            h = self._orb.height() * sc
            p.drawPixmap(QRectF(cx - w / 2, cy - h / 2, w, h), self._orb,
                         QRectF(self._orb.rect()))

        # название
        f = QFont()
        f.setPointSize(20)
        f.setWeight(QFont.Black)
        f.setLetterSpacing(QFont.AbsoluteSpacing, 7)
        p.setFont(f)
        p.setPen(QColor("#EDF3FF"))
        p.drawText(QRectF(0, 212, r.width(), 34), Qt.AlignCenter, "LIFE OS")

        f2 = QFont()
        f2.setPointSize(8)
        f2.setWeight(QFont.DemiBold)
        f2.setLetterSpacing(QFont.AbsoluteSpacing, 2.4)
        p.setFont(f2)
        p.setPen(QColor(acc.primary))
        p.drawText(QRectF(0, 246, r.width(), 20), Qt.AlignCenter,
                   f"ВЕРСИЯ {cfg.APP_VERSION}   ·   {cfg.DEV_NAME.upper()}")

        # прогресс
        val = self._progress.value / 100.0
        bar = QRectF(96, 310, r.width() - 192, 5)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 26))
        p.drawRoundedRect(bar, 2.5, 2.5)
        fill = QRectF(bar)
        fill.setWidth(max(3.0, bar.width() * val))
        g = QLinearGradient(bar.left(), 0, bar.right(), 0)
        g.setColorAt(0.0, QColor(acc.primary))
        g.setColorAt(1.0, QColor(acc.secondary))
        glow = QColor(acc.primary)
        glow.setAlphaF(0.34)
        p.setBrush(glow)
        p.drawRoundedRect(fill.adjusted(-1, -3, 1, 3), 5, 5)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(fill, 2.5, 2.5)

        label = STEPS[0][1]
        for th, name in STEPS:
            if val >= th:
                label = name
        f3 = QFont()
        f3.setPointSize(8)
        p.setFont(f3)
        p.setPen(QColor("#6B7A94"))
        p.drawText(QRectF(96, 322, bar.width(), 22),
                   Qt.AlignLeft | Qt.AlignVCenter, label)
        p.drawText(QRectF(96, 322, bar.width(), 22),
                   Qt.AlignRight | Qt.AlignVCenter, f"{int(val * 100)}%")

        p.setBrush(Qt.NoBrush)
        from PySide6.QtGui import QPen
        edge = QColor(acc.primary)
        edge.setAlpha(64)
        p.setPen(QPen(edge, 1))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), 22, 22)
        p.end()
