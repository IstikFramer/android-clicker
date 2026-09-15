"""LIFE OS — переиспользуемые визуальные компоненты (оболочка, без логики)."""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRect, QRectF, QSize,
    Property, Qt, QTimer, Signal,
)
from PySide6.QtGui import (
    QBrush, QColor, QConicalGradient, QFont, QIcon, QLinearGradient, QPainter,
    QPainterPath, QPen, QPixmap, QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from . import config as cfg
from .theme import ACCENTS

_pixmap_cache: dict[tuple[str, int, int], QPixmap] = {}


def load_pixmap(path: Path | str, w: int = 0, h: int = 0) -> QPixmap:
    """Загрузка картинки с кэшем и мягким масштабированием."""
    key = (str(path), w, h)
    if key in _pixmap_cache:
        return _pixmap_cache[key]
    pm = QPixmap(str(path))
    if not pm.isNull() and (w or h):
        if w and h:
            pm = pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        elif w:
            pm = pm.scaledToWidth(w, Qt.SmoothTransformation)
        else:
            pm = pm.scaledToHeight(h, Qt.SmoothTransformation)
    _pixmap_cache[key] = pm
    return pm


def glow(widget: QWidget, color: str = "#00E5FF", radius: int = 34, alpha: int = 90, dy: int = 6):
    """Неоновая тень-свечение под виджет."""
    eff = QGraphicsDropShadowEffect(widget)
    col = QColor(color)
    col.setAlpha(alpha)
    eff.setColor(col)
    eff.setBlurRadius(radius)
    eff.setOffset(0, dy)
    widget.setGraphicsEffect(eff)
    return eff


# ---------------------------------------------------------------------------
class BackgroundCanvas(QWidget):
    """Фон окна: 4K-картинка + затемнение + мягкие цветные блики."""

    def __init__(self, parent=None, image: str = "bg_main.jpg", accent: str = "cyan"):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._image = image
        self._accent = accent
        self._src = QPixmap(str(cfg.BACKGROUNDS / image))
        self._scaled: QPixmap | None = None
        self._phase = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)

    def set_image(self, image: str):
        self._image = image
        self._src = QPixmap(str(cfg.BACKGROUNDS / image))
        self._scaled = None
        self.update()

    def set_accent(self, accent: str):
        self._accent = accent
        self.update()

    def _tick(self):
        self._phase = (self._phase + 0.0045) % (math.pi * 2)
        self.update()

    def resizeEvent(self, e):
        self._scaled = None
        super().resizeEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = self.rect()

        path = QPainterPath()
        path.addRoundedRect(QRectF(r), cfg.WINDOW_RADIUS, cfg.WINDOW_RADIUS)
        p.setClipPath(path)

        p.fillRect(r, QColor("#05070D"))

        if not self._src.isNull():
            if self._scaled is None or self._scaled.size() != r.size():
                self._scaled = self._src.scaled(
                    r.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            sx = (self._scaled.width() - r.width()) // 2
            sy = (self._scaled.height() - r.height()) // 2
            p.drawPixmap(r, self._scaled, QRect(sx, sy, r.width(), r.height()))

        # затемнение, чтобы UI читался
        veil = QLinearGradient(0, 0, r.width(), r.height())
        veil.setColorAt(0.0, QColor(5, 7, 13, 205))
        veil.setColorAt(0.5, QColor(5, 7, 13, 232))
        veil.setColorAt(1.0, QColor(5, 7, 13, 210))
        p.fillRect(r, QBrush(veil))

        # два «дышащих» неоновых блика
        acc = ACCENTS.get(self._accent, ACCENTS["cyan"])
        c1 = QColor(acc.primary)
        c2 = QColor(acc.secondary)
        for col, cx, cy, rad, base, ph in (
            (c1, 0.16, 0.10, 0.62, 34, 0.0),
            (c2, 0.88, 0.92, 0.70, 30, math.pi * 0.7),
        ):
            pulse = 0.5 + 0.5 * math.sin(self._phase + ph)
            g = QRadialGradient(
                QPointF(r.width() * cx, r.height() * cy), max(r.width(), r.height()) * rad
            )
            cc = QColor(col)
            cc.setAlpha(int(base + pulse * 16))
            g.setColorAt(0.0, cc)
            cc2 = QColor(col)
            cc2.setAlpha(0)
            g.setColorAt(1.0, cc2)
            p.fillRect(r, QBrush(g))

        # тонкая внутренняя окантовка стекла
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5),
                          cfg.WINDOW_RADIUS, cfg.WINDOW_RADIUS)
        p.end()


# ---------------------------------------------------------------------------
class GlassCard(QFrame):
    """Полупрозрачная стеклянная карточка с мягким свечением."""

    def __init__(self, parent=None, hoverable: bool = True, padding: int = 20,
                 spacing: int = 12, accent: str = "#00E5FF"):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setProperty("hoverable", "true" if hoverable else "false")
        self.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(padding, padding, padding, padding)
        lay.setSpacing(spacing)
        self.body = lay
        eff = QGraphicsDropShadowEffect(self)
        eff.setColor(QColor(0, 0, 0, 150))
        eff.setBlurRadius(38)
        eff.setOffset(0, 12)
        self.setGraphicsEffect(eff)


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarDivider")
        self.setFixedHeight(1)
        self.setAttribute(Qt.WA_StyledBackground, True)


# ---------------------------------------------------------------------------
class NavButton(QPushButton):
    """Пункт бокового меню: иконка + подпись + неоновый индикатор слева."""

    def __init__(self, text: str, icon_path: Path | str, parent=None, accent: str = "#00E5FF"):
        super().__init__(parent)
        self.setObjectName("NavItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self._full_text = text
        self._accent = accent
        self._collapsed = False
        self.setIcon(QIcon(str(icon_path)))
        self.setIconSize(QSize(22, 22))
        self.setText("   " + text)

    def set_accent(self, color: str):
        self._accent = color
        self.update()

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self.setText("" if collapsed else "   " + self._full_text)
        self.setToolTip(self._full_text if collapsed else "")
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self.isChecked():
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        col = QColor(self._accent)
        h = self.height()
        bar = QRectF(3, h * 0.24, 3.4, h * 0.52)
        gl = QColor(col)
        gl.setAlpha(70)
        p.setPen(Qt.NoPen)
        p.setBrush(gl)
        p.drawRoundedRect(bar.adjusted(-2.5, -2.5, 2.5, 2.5), 5, 5)
        p.setBrush(col)
        p.drawRoundedRect(bar, 2, 2)
        p.end()


# ---------------------------------------------------------------------------
class PulseLine(QWidget):
    """Живая линия пульса — декоративный «сигнал жизни» системы."""

    def __init__(self, parent=None, accent: str = "#00E5FF", height: int = 64):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._accent = accent
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(33)

    def set_accent(self, color: str):
        self._accent = color

    def _tick(self):
        self._t += 0.055
        self.update()

    @staticmethod
    def _beat(x: float) -> float:
        """Форма кардио-импульса в зависимости от фазы 0..1."""
        d = (x % 1.0) * 10.0
        if 3.6 <= d < 4.1:
            return -0.28
        if 4.1 <= d < 4.5:
            return 1.0
        if 4.5 <= d < 4.9:
            return -0.62
        if 4.9 <= d < 5.3:
            return 0.22
        return 0.0

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        mid = h / 2
        col = QColor(self._accent)

        path = QPainterPath()
        steps = max(80, w // 3)
        for i in range(steps + 1):
            x = w * i / steps
            phase = x / max(w, 1) * 2.0 - self._t * 0.28
            v = self._beat(phase)
            v += 0.05 * math.sin(x * 0.055 + self._t * 1.5)
            y = mid - v * (h * 0.36)
            path.lineTo(x, y) if i else path.moveTo(x, y)

        halo = QColor(col)
        halo.setAlpha(46)
        p.setPen(QPen(halo, 7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(path)
        halo.setAlpha(96)
        p.setPen(QPen(halo, 3.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(path)
        p.setPen(QPen(col, 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(path)
        p.end()


# ---------------------------------------------------------------------------
class RingGauge(QWidget):
    """Кольцевой индикатор с градиентом и плавной анимацией значения."""

    def __init__(self, parent=None, value: float = 0.0, caption: str = "",
                 accent: str = "#00E5FF", accent2: str = "#2D7FF9", size: int = 132):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._value = 0.0
        self._target = value
        self._caption = caption
        self._accent = accent
        self._accent2 = accent2
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def set_value(self, v: float):
        self._target = max(0.0, min(100.0, v))

    def set_accent(self, a: str, a2: str):
        self._accent, self._accent2 = a, a2
        self.update()

    def _tick(self):
        if abs(self._value - self._target) < 0.05:
            return
        self._value += (self._target - self._value) * 0.08
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        side = min(self.width(), self.height())
        pad = 11
        rect = QRectF(pad, pad, side - pad * 2, side - pad * 2)

        p.setPen(QPen(QColor(255, 255, 255, 20), 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 0, 360 * 16)

        grad = QConicalGradient(rect.center(), 90)
        grad.setColorAt(0.0, QColor(self._accent))
        grad.setColorAt(0.5, QColor(self._accent2))
        grad.setColorAt(1.0, QColor(self._accent))
        span = int(-self._value / 100.0 * 360 * 16)

        halo = QColor(self._accent)
        halo.setAlpha(60)
        p.setPen(QPen(halo, 15, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, span)
        p.setPen(QPen(QBrush(grad), 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, span)

        f = QFont()
        f.setPointSizeF(side * 0.155)
        f.setWeight(QFont.Black)
        p.setFont(f)
        p.setPen(QColor("#EAF2FF"))
        p.drawText(rect, Qt.AlignCenter, f"{int(round(self._value))}%")

        if self._caption:
            f2 = QFont()
            f2.setPointSizeF(side * 0.068)
            f2.setWeight(QFont.DemiBold)
            p.setFont(f2)
            p.setPen(QColor("#6B7A94"))
            p.drawText(QRectF(0, side * 0.66, side, side * 0.2),
                       Qt.AlignHCenter | Qt.AlignTop, self._caption)
        p.end()


# ---------------------------------------------------------------------------
class SparkChart(QWidget):
    """Декоративный график-волна для карточек статистики."""

    def __init__(self, parent=None, accent: str = "#00E5FF", points: int = 44, height: int = 74):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._accent = accent
        self._n = points
        self._t = 0.0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(60)

    def set_accent(self, color: str):
        self._accent = color

    def _tick(self):
        self._t += 0.06
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        col = QColor(self._accent)

        pts: list[QPointF] = []
        for i in range(self._n):
            x = w * i / (self._n - 1)
            u = i / (self._n - 1)
            v = (
                0.50
                + 0.22 * math.sin(u * 7.0 + self._t)
                + 0.13 * math.sin(u * 13.0 - self._t * 1.6)
                + 0.07 * math.sin(u * 23.0 + self._t * 0.7)
            )
            pts.append(QPointF(x, h - v * h * 0.86 - h * 0.07))

        line = QPainterPath(pts[0])
        for pt in pts[1:]:
            line.lineTo(pt)

        area = QPainterPath(line)
        area.lineTo(w, h)
        area.lineTo(0, h)
        area.closeSubpath()

        g = QLinearGradient(0, 0, 0, h)
        c1 = QColor(col); c1.setAlpha(80)
        c2 = QColor(col); c2.setAlpha(0)
        g.setColorAt(0.0, c1)
        g.setColorAt(1.0, c2)
        p.fillPath(area, QBrush(g))

        halo = QColor(col); halo.setAlpha(70)
        p.setPen(QPen(halo, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(line)
        p.setPen(QPen(col, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawPath(line)
        p.end()


# ---------------------------------------------------------------------------
class LogoBadge(QWidget):
    """Логотип с вращающимся орбитальным кольцом вокруг."""

    def __init__(self, parent=None, size: int = 44, accent: str = "#00E5FF",
                 pixmap_name: str = "logo_mini_256.png", spin: bool = True):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._accent = accent
        self._angle = 0.0
        self._spin = spin
        self._pm = load_pixmap(cfg.LOGO / pixmap_name, int(size * 0.78), int(size * 0.78))
        if spin:
            self._timer = QTimer(self)
            self._timer.timeout.connect(self._tick)
            self._timer.start(33)

    def set_accent(self, color: str):
        self._accent = color
        self.update()

    def _tick(self):
        self._angle = (self._angle + 1.1) % 360
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        s = min(self.width(), self.height())
        col = QColor(self._accent)

        g = QRadialGradient(QPointF(s / 2, s / 2), s / 2)
        c = QColor(col); c.setAlpha(58)
        g.setColorAt(0.0, c)
        c0 = QColor(col); c0.setAlpha(0)
        g.setColorAt(1.0, c0)
        p.fillRect(self.rect(), QBrush(g))

        if self._spin:
            rect = QRectF(1.5, 1.5, s - 3, s - 3)
            ring = QColor(col); ring.setAlpha(150)
            p.setPen(QPen(ring, 1.6, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int(self._angle * 16), 100 * 16)
            ring.setAlpha(60)
            p.setPen(QPen(ring, 1.2, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, int((self._angle + 180) * 16), 60 * 16)

        if not self._pm.isNull():
            p.drawPixmap(
                int((s - self._pm.width()) / 2),
                int((s - self._pm.height()) / 2),
                self._pm,
            )
        p.end()


# ---------------------------------------------------------------------------
class ImagePanel(QFrame):
    """Панель с фоновой картинкой, скруглением и затемнением под текст."""

    def __init__(self, image_path: Path | str, parent=None, radius: int = 22,
                 overlay: float = 0.55, accent: str = "#00E5FF"):
        super().__init__(parent)
        self.setObjectName("HeroCard")
        self._src = QPixmap(str(image_path))
        self._scaled: QPixmap | None = None
        self._radius = radius
        self._overlay = overlay
        self._accent = accent
        eff = QGraphicsDropShadowEffect(self)
        eff.setColor(QColor(0, 0, 0, 170))
        eff.setBlurRadius(46)
        eff.setOffset(0, 16)
        self.setGraphicsEffect(eff)

    def set_accent(self, color: str):
        self._accent = color
        self.update()

    def resizeEvent(self, e):
        self._scaled = None
        super().resizeEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = self.rect()
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), self._radius, self._radius)
        p.setClipPath(path)
        p.fillRect(r, QColor("#070A12"))

        if not self._src.isNull() and r.width() > 0 and r.height() > 0:
            if self._scaled is None or self._scaled.size() != r.size():
                self._scaled = self._src.scaled(
                    r.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
            sx = (self._scaled.width() - r.width()) // 2
            sy = (self._scaled.height() - r.height()) // 2
            p.drawPixmap(r, self._scaled, QRect(sx, sy, r.width(), r.height()))

        g = QLinearGradient(0, 0, r.width(), 0)
        g.setColorAt(0.0, QColor(5, 7, 13, int(255 * min(0.96, self._overlay + 0.32))))
        g.setColorAt(0.62, QColor(5, 7, 13, int(255 * self._overlay)))
        g.setColorAt(1.0, QColor(5, 7, 13, int(255 * max(0.0, self._overlay - 0.28))))
        p.fillRect(r, QBrush(g))

        p.setBrush(Qt.NoBrush)
        edge = QColor(self._accent)
        edge.setAlpha(60)
        p.setPen(QPen(edge, 1))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), self._radius, self._radius)
        p.end()


# ---------------------------------------------------------------------------
def make_label(text: str, obj: str, parent=None, wrap: bool = False) -> QLabel:
    lb = QLabel(text, parent)
    lb.setObjectName(obj)
    lb.setWordWrap(wrap)
    return lb


def row(*widgets: QWidget, spacing: int = 10, stretch_last: bool = False) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    for item in widgets:
        lay.addWidget(item)
    if stretch_last:
        lay.addStretch(1)
    return w


def fade_in(widget: QWidget, duration: int = 260, delay: int = 0) -> QPropertyAnimation:
    """Плавное появление виджета."""
    eff = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(eff)
    eff.setOpacity(0.0)
    anim = QPropertyAnimation(eff, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    widget._fade_anim = anim  # держим ссылку
    QTimer.singleShot(delay, anim.start)
    return anim
