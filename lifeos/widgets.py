"""LIFE OS — библиотека визуальных компонентов.

Все анимации идут через общий движок (lifeos.anim), поэтому кадры ровные,
частота ограничена настройками, а при отключённых анимациях виджеты
просто перестают получать такты и не тратят ресурсы.
"""
from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import (
    QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer,
    Signal,
)
from PySide6.QtGui import (
    QBrush, QColor, QConicalGradient, QFont, QFontMetrics, QGuiApplication,
    QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient,
)
from PySide6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from . import config as cfg
from . import icons
from .anim import Spring, driver
from .settings import settings
from .theme import current_accent

_pm_cache: dict[tuple, QPixmap] = {}


class GlowAware:
    """Метка для виджетов, которые сами рисуют неоновое свечение.

    По ней окно понимает, что именно нужно перерисовать при изменении
    ползунка «Сила свечения». Карточки с тенями в список не входят:
    их update() заставляет Qt заново считать размытие в пиксмап, а это
    и было причиной подтормаживания ползунков.
    """


def load_pixmap(path: Path | str, w: int = 0, h: int = 0) -> QPixmap:
    key = (str(path), w, h)
    if key not in _pm_cache:
        pm = QPixmap(str(path))
        if not pm.isNull() and (w or h):
            if w and h:
                pm = pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            elif w:
                pm = pm.scaledToWidth(w, Qt.SmoothTransformation)
            else:
                pm = pm.scaledToHeight(h, Qt.SmoothTransformation)
        _pm_cache[key] = pm
    return _pm_cache[key]


def make_label(text: str, obj: str, parent=None, wrap: bool = False) -> QLabel:
    lb = QLabel(text, parent)
    lb.setObjectName(obj)
    lb.setWordWrap(wrap)
    if wrap:
        lb.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
    return lb


def soft_shadow(widget: QWidget, blur: int = 40, alpha: int = 150, dy: int = 12):
    if not settings.get("heavy_effects"):
        widget.setGraphicsEffect(None)
        return None
    eff = QGraphicsDropShadowEffect(widget)
    eff.setColor(QColor(0, 0, 0, alpha))
    eff.setBlurRadius(blur)
    eff.setOffset(0, dy)
    widget.setGraphicsEffect(eff)
    return eff


# ===========================================================================
class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Divider")
        self.setFixedHeight(1)
        self.setAttribute(Qt.WA_StyledBackground, True)


# ===========================================================================
class BackgroundCanvas(GlowAware, QWidget):
    """Фон окна: изображение, затемнение и два медленно дышащих блика.

    Статичная часть (картинка + затемнение + рамка) собирается в кэш-пиксмап
    один раз на размер окна, а каждый кадр рисуется только готовый кэш плюс
    два заранее отрендеренных пятна свечения. Благодаря этому фон перестал
    съедать кадры: раньше полноэкранный градиент пересчитывался 60 раз в
    секунду и ронял частоту до 25 FPS.
    """

    _GLOW_TEX = 192  # размер текстуры свечения

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self._src = QPixmap()
        self._base: QPixmap | None = None
        self._glow: QPixmap | None = None
        self._glow_key: tuple = ()
        self._phase = 0.0
        self._accum = 0.0
        self.reload()
        driver().subscribe(self, self._tick)

    # ------------------------------------------------------------- ресурсы
    def reload(self):
        self._src = QPixmap(str(cfg.BACKGROUNDS / settings.get("background")))
        self._base = None
        self.update()

    def invalidate(self):
        self._base = None
        self._glow = None
        self.update()

    def _build_base(self):
        r = self.rect()
        if r.width() < 2 or r.height() < 2:
            return
        pm = QPixmap(r.size())
        pm.fill(QColor("#04060C"))
        p = QPainter(pm)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        rad = settings.get("corner_radius")
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), rad, rad)
        p.setClipPath(path)

        if not self._src.isNull():
            sc = self._src.scaled(r.size(), Qt.KeepAspectRatioByExpanding,
                                  Qt.SmoothTransformation)
            p.drawPixmap(r, sc, QRect((sc.width() - r.width()) // 2,
                                      (sc.height() - r.height()) // 2,
                                      r.width(), r.height()))
        veil = QLinearGradient(0, 0, r.width(), r.height())
        veil.setColorAt(0.0, QColor(4, 6, 12, 200))
        veil.setColorAt(0.5, QColor(4, 6, 12, 228))
        veil.setColorAt(1.0, QColor(4, 6, 12, 206))
        p.fillRect(r, QBrush(veil))

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 24), 1))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        p.end()
        self._base = pm

    def _build_glow(self):
        """Круглая текстура свечения — рисуется один раз, затем растягивается."""
        acc = current_accent()
        key = (acc.primary, acc.secondary)
        if self._glow is not None and self._glow_key == key:
            return
        n = self._GLOW_TEX
        pm = QPixmap(n * 2, n)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        for i, col in enumerate((QColor(acc.primary), QColor(acc.secondary))):
            g = QRadialGradient(QPointF(n * i + n / 2, n / 2), n / 2)
            c = QColor(col)
            c.setAlpha(255)
            g.setColorAt(0.0, c)
            mid = QColor(col)
            mid.setAlpha(90)
            g.setColorAt(0.45, mid)
            c0 = QColor(col)
            c0.setAlpha(0)
            g.setColorAt(1.0, c0)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawRect(n * i, 0, n, n)
        p.end()
        self._glow = pm
        self._glow_key = key

    # --------------------------------------------------------------- кадр
    def _tick(self, dt: float):
        if not settings.get("heavy_effects") or settings.glow_alpha <= 0.02:
            return
        self._phase = (self._phase + dt * 0.22) % (math.pi * 2)
        # блики дышат очень медленно, поэтому фону хватает ~20 кадров в секунду.
        # Перерисовывать его синхронно с интерфейсом незачем: это полноэкранная
        # операция, которая забирала бы кадры у отзывчивых элементов.
        self._accum += dt
        if self._accum < 0.05:
            return
        self._accum = 0.0
        self.update()

    def resizeEvent(self, e):
        self._base = None
        super().resizeEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        r = self.rect()
        if self._base is None or self._base.size() != r.size():
            self._build_base()
        if self._base is not None:
            p.drawPixmap(0, 0, self._base)

        strength = settings.glow_alpha
        if strength <= 0.02 or not settings.get("heavy_effects"):
            p.end()
            return

        self._build_glow()
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        n = self._GLOW_TEX
        size = max(r.width(), r.height()) * 1.45
        for idx, (cx, cy, base, ph) in enumerate((
            (0.14, 0.08, 0.13, 0.0),
            (0.90, 0.94, 0.11, 2.2),
        )):
            pulse = 0.5 + 0.5 * math.sin(self._phase + ph)
            p.setOpacity(min(0.6, (base + pulse * 0.05) * strength))
            p.drawPixmap(
                QRectF(r.width() * cx - size / 2, r.height() * cy - size / 2, size, size),
                self._glow, QRectF(n * idx, 0, n, n))
        p.setOpacity(1.0)
        p.end()


# ===========================================================================
class GlassCard(QFrame):
    """Стеклянная карточка. При наведении мягко подсвечивается и приподнимается."""

    def __init__(self, parent=None, hoverable: bool = True, padding: int = 20,
                 spacing: int = 12):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._hoverable = hoverable
        self._hover = Spring(0.0, 14.0)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(padding, padding, padding, padding)
        lay.setSpacing(spacing)
        self.body = lay
        soft_shadow(self, 38, 140, 10)
        if hoverable:
            self.setAttribute(Qt.WA_Hover, True)
            driver().subscribe(self, self._tick)

    def enterEvent(self, e):
        if self._hoverable:
            self._hover.set(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover.set(0.0)
        super().leaveEvent(e)

    def _tick(self, dt: float):
        if self._hover.done:
            return
        self._hover.step(dt)
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        v = self._hover.value
        if v < 0.01:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rad = settings.get("corner_radius")
        acc = current_accent()
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        wash = QColor(acc.primary)
        wash.setAlphaF(0.05 * v)
        p.setPen(Qt.NoPen)
        p.setBrush(wash)
        p.drawRoundedRect(r, rad, rad)

        edge = QColor(acc.primary)
        edge.setAlphaF(0.45 * v)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(edge, 1.2))
        p.drawRoundedRect(r, rad, rad)
        p.end()


# ===========================================================================
class ImagePanel(QFrame):
    """Панель с фоновой картинкой, затемнением и скруглением."""

    def __init__(self, image_path: Path | str, parent=None, overlay: float = 0.55,
                 radius: int | None = None, gradient_dir: str = "h"):
        super().__init__(parent)
        self.setObjectName("HeroCard")
        self._src = QPixmap(str(image_path))
        self._scaled: QPixmap | None = None
        self._overlay = overlay
        self._radius = radius
        self._dir = gradient_dir
        soft_shadow(self, 46, 170, 14)

    def set_image(self, path: Path | str):
        self._src = QPixmap(str(path))
        self._scaled = None
        self.update()

    def resizeEvent(self, e):
        self._scaled = None
        super().resizeEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        r = self.rect()
        if r.width() < 2 or r.height() < 2:
            return
        rad = self._radius if self._radius is not None else settings.get("corner_radius")
        path = QPainterPath()
        path.addRoundedRect(QRectF(r), rad, rad)
        p.setClipPath(path)
        p.fillRect(r, QColor("#05080F"))

        if not self._src.isNull():
            if self._scaled is None or self._scaled.size() != r.size():
                self._scaled = self._src.scaled(
                    r.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            sx = (self._scaled.width() - r.width()) // 2
            sy = (self._scaled.height() - r.height()) // 2
            p.drawPixmap(r, self._scaled, QRect(sx, sy, r.width(), r.height()))

        g = (QLinearGradient(0, 0, r.width(), 0) if self._dir == "h"
             else QLinearGradient(0, 0, 0, r.height()))
        o = self._overlay
        g.setColorAt(0.0, QColor(4, 6, 12, int(255 * min(0.97, o + 0.34))))
        g.setColorAt(0.60, QColor(4, 6, 12, int(255 * o)))
        g.setColorAt(1.0, QColor(4, 6, 12, int(255 * max(0.0, o - 0.30))))
        p.fillRect(r, QBrush(g))

        acc = current_accent()
        edge = QColor(acc.primary)
        edge.setAlpha(int(55 * min(1.0, settings.glow_alpha + 0.3)))
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(edge, 1))
        p.drawRoundedRect(QRectF(r).adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        p.end()


# ===========================================================================
class NavButton(QPushButton):
    """Пункт бокового меню: SVG-иконка, подпись, плавная подсветка и индикатор."""

    def __init__(self, text: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("NavItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(46)
        self.setAttribute(Qt.WA_Hover, True)
        self._label = text
        self._icon_name = icon_name
        self._collapsed = False
        self._sel = Spring(0.0, 15.0)
        self._hov = Spring(0.0, 18.0)
        driver().subscribe(self, self._tick)

    def set_collapsed(self, collapsed: bool):
        self._collapsed = collapsed
        self.setToolTip(self._label if collapsed else "")
        self.update()

    def setChecked(self, on: bool):
        super().setChecked(on)
        self._sel.set(1.0 if on else 0.0)
        self.update()

    def enterEvent(self, e):
        self._hov.set(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hov.set(0.0)
        super().leaveEvent(e)

    def _tick(self, dt: float):
        if self._sel.done and self._hov.done:
            return
        self._sel.step(dt)
        self._hov.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        acc = current_accent()
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        rad = max(8, int(settings.get("corner_radius") * 0.66))
        sel, hov = self._sel.value, self._hov.value

        if hov > 0.01 and sel < 0.99:
            c = QColor(255, 255, 255)
            c.setAlphaF(0.05 * hov * (1 - sel))
            p.setPen(Qt.NoPen)
            p.setBrush(c)
            p.drawRoundedRect(r, rad, rad)

        if sel > 0.01:
            g = QLinearGradient(r.left(), 0, r.right(), 0)
            c1 = QColor(acc.primary)
            c1.setAlphaF(0.22 * sel)
            c2 = QColor(acc.primary)
            c2.setAlphaF(0.02 * sel)
            g.setColorAt(0.0, c1)
            g.setColorAt(1.0, c2)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(r, rad, rad)
            edge = QColor(acc.primary)
            edge.setAlphaF(0.38 * sel)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(edge, 1))
            p.drawRoundedRect(r, rad, rad)

            h = self.height()
            bar = QRectF(4, h / 2 - h * 0.26 * sel, 3.2, h * 0.52 * sel)
            p.setPen(Qt.NoPen)
            halo = QColor(acc.primary)
            halo.setAlphaF(0.30 * sel)
            p.setBrush(halo)
            p.drawRoundedRect(bar.adjusted(-2.5, -2.5, 2.5, 2.5), 5, 5)
            p.setBrush(QColor(acc.primary))
            p.drawRoundedRect(bar, 2, 2)

        # иконка: цвет плавно уходит в акцент при выборе
        base = QColor("#9DABC2")
        act = QColor(acc.primary)
        mix = QColor(
            int(base.red() + (act.red() - base.red()) * max(sel, hov * 0.55)),
            int(base.green() + (act.green() - base.green()) * max(sel, hov * 0.55)),
            int(base.blue() + (act.blue() - base.blue()) * max(sel, hov * 0.55)),
        )
        pm = icons.pixmap(self._icon_name, 21, mix.name(), 1.75)
        ix = 21 if self._collapsed else 18
        p.drawPixmap(int((self.width() - 21) / 2) if self._collapsed else ix,
                     int((self.height() - 21) / 2), pm)

        if not self._collapsed:
            f = self.font()
            f.setPointSizeF(max(8.0, 9.8 * settings.get("ui_scale") / 100))
            f.setWeight(QFont.DemiBold if sel < 0.5 else QFont.Bold)
            p.setFont(f)
            tc = QColor("#EDF3FF") if sel > 0.5 else QColor("#9DABC2")
            if sel <= 0.5 and hov > 0.01:
                tc = QColor("#EDF3FF") if hov > 0.6 else tc
            p.setPen(tc)
            p.drawText(QRectF(50, 0, self.width() - 60, self.height()),
                       Qt.AlignVCenter | Qt.AlignLeft, self._label)
        p.end()


# ===========================================================================
class IconButton(QPushButton):
    """Круглая/квадратная кнопка с SVG-иконкой и плавным hover."""

    def __init__(self, icon_name: str, size: int = 34, icon_size: int = 18,
                 parent=None, danger: bool = False, tooltip: str = ""):
        super().__init__(parent)
        self.setObjectName("WinBtnClose" if danger else "WinBtn")
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._icon_name = icon_name
        self._isize = icon_size
        self._danger = danger
        self._hov = Spring(0.0, 20.0)
        if tooltip:
            self.setToolTip(tooltip)
        driver().subscribe(self, self._tick)

    def set_icon_name(self, name: str):
        self._icon_name = name
        self.update()

    def enterEvent(self, e):
        self._hov.set(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hov.set(0.0)
        super().leaveEvent(e)

    def _tick(self, dt: float):
        if self._hov.done:
            return
        self._hov.step(dt)
        self.update()

    def paintEvent(self, e):
        super().paintEvent(e)
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        v = self._hov.value
        base = QColor("#9DABC2")
        target = QColor("#FF5C6C") if self._danger else QColor("#EDF3FF")
        col = QColor(
            int(base.red() + (target.red() - base.red()) * v),
            int(base.green() + (target.green() - base.green()) * v),
            int(base.blue() + (target.blue() - base.blue()) * v),
        )
        pm = icons.pixmap(self._icon_name, self._isize, col.name(), 1.8)
        p.drawPixmap(int((self.width() - self._isize) / 2),
                     int((self.height() - self._isize) / 2), pm)
        p.end()


# ===========================================================================
class Switch(GlowAware, QWidget):
    """Переключатель с анимированным ползунком."""

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(46, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._on = checked
        self._pos = Spring(1.0 if checked else 0.0, 18.0)
        driver().subscribe(self, self._tick)

    def isChecked(self) -> bool:
        return self._on

    def setChecked(self, on: bool, emit: bool = False):
        if self._on == on:
            return
        self._on = on
        self._pos.set(1.0 if on else 0.0)
        self.update()
        if emit:
            self.toggled.emit(on)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.setChecked(not self._on, emit=True)
        super().mousePressEvent(e)

    def _tick(self, dt: float):
        if self._pos.done:
            return
        self._pos.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = current_accent()
        v = self._pos.value
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)

        off = QColor(255, 255, 255, 26)
        on1, on2 = QColor(acc.primary), QColor(acc.secondary)
        if v < 0.999:
            p.setPen(Qt.NoPen)
            p.setBrush(off)
            p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        if v > 0.001:
            g = QLinearGradient(r.left(), 0, r.right(), 0)
            on1.setAlphaF(v)
            on2.setAlphaF(v)
            g.setColorAt(0.0, on1)
            g.setColorAt(1.0, on2)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(r, r.height() / 2, r.height() / 2)

        p.setBrush(Qt.NoBrush)
        edge = QColor(255, 255, 255, 40)
        p.setPen(QPen(edge, 1))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)

        d = self.height() - 8
        x = 4 + v * (self.width() - d - 8)
        knob = QRectF(x, 4, d, d)
        p.setPen(Qt.NoPen)
        if v > 0.3:
            halo = QColor(acc.primary)
            halo.setAlphaF(0.35 * v * min(1.0, settings.glow_alpha + 0.3))
            p.setBrush(halo)
            p.drawEllipse(knob.adjusted(-3, -3, 3, 3))
        p.setBrush(QColor("#FFFFFF") if v > 0.5 else QColor("#C8D3E6"))
        p.drawEllipse(knob)
        p.end()


# ===========================================================================
class Slider(GlowAware, QWidget):
    """Слайдер: неоновая шкала, перетаскиваемая ручка, подпись значения."""

    valueChanged = Signal(int)

    def __init__(self, minimum: int = 0, maximum: int = 100, value: int = 50,
                 step: int = 1, suffix: str = "", parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setMinimumWidth(180)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._min, self._max, self._step = minimum, maximum, step
        self._value = max(minimum, min(maximum, value))
        self._vis = Spring(float(self._value), 22.0)
        self._hov = Spring(0.0, 18.0)
        self._drag = False
        driver().subscribe(self, self._tick)
        self._suffix = suffix

    # ------------------------------------------------------------ значение
    def value(self) -> int:
        return self._value

    def setValue(self, v: int, emit: bool = True):
        v = int(round(max(self._min, min(self._max, v)) / self._step) * self._step)
        if v == self._value:
            return
        self._value = v
        self._vis.set(float(v))
        self.update()
        if emit:
            self.valueChanged.emit(v)

    def _track(self) -> QRectF:
        return QRectF(9, self.height() / 2 - 3, self.width() - 18, 6)

    def _from_x(self, x: float) -> int:
        t = self._track()
        ratio = (x - t.left()) / max(1.0, t.width())
        return round(self._min + max(0.0, min(1.0, ratio)) * (self._max - self._min))

    # -------------------------------------------------------------- ввод
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = True
            self.setValue(self._from_x(e.position().x()))
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag:
            self.setValue(self._from_x(e.position().x()))
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag = False
        super().mouseReleaseEvent(e)

    def wheelEvent(self, e):
        self.setValue(self._value + (self._step if e.angleDelta().y() > 0 else -self._step))
        e.accept()

    def enterEvent(self, e):
        self._hov.set(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hov.set(0.0)
        super().leaveEvent(e)

    def _tick(self, dt: float):
        if self._vis.done and self._hov.done:
            return
        self._vis.step(dt)
        self._hov.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = current_accent()
        t = self._track()
        ratio = (self._vis.value - self._min) / max(1e-6, self._max - self._min)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 24))
        p.drawRoundedRect(t, 3, 3)

        fill = QRectF(t)
        fill.setWidth(max(6.0, t.width() * ratio))
        g = QLinearGradient(t.left(), 0, t.right(), 0)
        g.setColorAt(0.0, QColor(acc.primary))
        g.setColorAt(1.0, QColor(acc.secondary))
        glow_a = settings.glow_alpha
        if glow_a > 0.05:
            halo = QColor(acc.primary)
            halo.setAlphaF(min(0.35, 0.26 * glow_a))
            p.setBrush(halo)
            p.drawRoundedRect(fill.adjusted(-1, -3.5, 1, 3.5), 6, 6)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(fill, 3, 3)

        d = 15 + 2.5 * self._hov.value
        cx = t.left() + t.width() * ratio
        knob = QRectF(cx - d / 2, self.height() / 2 - d / 2, d, d)
        if glow_a > 0.05:
            halo = QColor(acc.primary)
            halo.setAlphaF(min(0.45, 0.32 * glow_a))
            p.setBrush(halo)
            p.drawEllipse(knob.adjusted(-4, -4, 4, 4))
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(knob)
        p.setBrush(QColor(acc.primary))
        p.drawEllipse(knob.adjusted(d * 0.30, d * 0.30, -d * 0.30, -d * 0.30))
        p.end()


class SliderRow(QWidget):
    """Строка настройки: название, описание, слайдер и текущее значение."""

    valueChanged = Signal(int)

    def __init__(self, title: str, desc: str, minimum: int, maximum: int,
                 value: int, suffix: str = "", step: int = 1, parent=None):
        super().__init__(parent)
        self._suffix = suffix
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 10, 0, 10)
        lay.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(10)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label(title, "CardTitle"))
        if desc:
            col.addWidget(make_label(desc, "Caption"))
        head.addLayout(col)
        head.addStretch(1)
        self.value_label = make_label(f"{value}{suffix}", "MonoAccent")
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.value_label.setFixedWidth(64)
        head.addWidget(self.value_label)
        lay.addLayout(head)

        self.slider = Slider(minimum, maximum, value, step, suffix)
        self.slider.valueChanged.connect(self._on_change)
        lay.addWidget(self.slider)

    def _on_change(self, v: int):
        self.value_label.setText(f"{v}{self._suffix}")
        self.valueChanged.emit(v)

    def value(self) -> int:
        return self.slider.value()

    def setValue(self, v: int):
        self.slider.setValue(v)


# ===========================================================================
class SegmentedControl(GlowAware, QWidget):
    """Переключатель вариантов с плавно скользящим выделением."""

    changed = Signal(int)

    def __init__(self, options: list[str], index: int = 0, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self._opts = options
        self._index = index
        self._pos = Spring(float(index), 20.0)
        driver().subscribe(self, self._tick)

    def currentIndex(self) -> int:
        return self._index

    def setCurrentIndex(self, i: int, emit: bool = False):
        i = max(0, min(len(self._opts) - 1, i))
        if i == self._index:
            return
        self._index = i
        self._pos.set(float(i))
        self.update()
        if emit:
            self.changed.emit(i)

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        w = sum(fm.horizontalAdvance(o) + 34 for o in self._opts) + 8
        return QSize(w, 36)

    def mousePressEvent(self, e):
        seg = (self.width() - 8) / len(self._opts)
        self.setCurrentIndex(int((e.position().x() - 4) / seg), emit=True)
        super().mousePressEvent(e)

    def _tick(self, dt: float):
        if self._pos.done:
            return
        self._pos.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = current_accent()
        r = QRectF(0.5, 0.5, self.width() - 1, self.height() - 1)
        rad = max(8, int(settings.get("corner_radius") * 0.55))

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 18))
        p.drawRoundedRect(r, rad, rad)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 255, 255, 26), 1))
        p.drawRoundedRect(r, rad, rad)

        seg = (self.width() - 8) / len(self._opts)
        sel = QRectF(4 + seg * self._pos.value, 4, seg, self.height() - 8)
        g = QLinearGradient(sel.left(), 0, sel.right(), 0)
        g.setColorAt(0.0, QColor(acc.primary))
        g.setColorAt(1.0, QColor(acc.secondary))
        if settings.glow_alpha > 0.05:
            halo = QColor(acc.primary)
            halo.setAlphaF(min(0.35, 0.25 * settings.glow_alpha))
            p.setPen(Qt.NoPen)
            p.setBrush(halo)
            p.drawRoundedRect(sel.adjusted(-2, -2, 2, 2), rad - 2, rad - 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawRoundedRect(sel, rad - 3, rad - 3)

        f = self.font()
        f.setPointSizeF(max(7.5, 9.0 * settings.get("ui_scale") / 100))
        f.setWeight(QFont.Bold)
        p.setFont(f)
        for i, opt in enumerate(self._opts):
            cell = QRectF(4 + seg * i, 4, seg, self.height() - 8)
            near = max(0.0, 1.0 - abs(self._pos.value - i))
            base = QColor("#9DABC2")
            over = QColor("#04121A")
            col = QColor(
                int(base.red() + (over.red() - base.red()) * near),
                int(base.green() + (over.green() - base.green()) * near),
                int(base.blue() + (over.blue() - base.blue()) * near),
            )
            p.setPen(col)
            p.drawText(cell, Qt.AlignCenter, opt)
        p.end()


# ===========================================================================
class ColorDot(GlowAware, QWidget):
    """Кружок выбора акцента с анимированным кольцом выбора."""

    clicked = Signal(str)

    def __init__(self, key: str, primary: str, secondary: str,
                 selected: bool = False, parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self._key = key
        self._c1, self._c2 = primary, secondary
        self._sel = Spring(1.0 if selected else 0.0, 18.0)
        self._hov = Spring(0.0, 20.0)
        driver().subscribe(self, self._tick)

    def setSelected(self, on: bool):
        self._sel.set(1.0 if on else 0.0)
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._key)
        super().mousePressEvent(e)

    def enterEvent(self, e):
        self._hov.set(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hov.set(0.0)
        super().leaveEvent(e)

    def _tick(self, dt: float):
        if self._sel.done and self._hov.done:
            return
        self._sel.step(dt)
        self._hov.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        s, h = self._sel.value, self._hov.value
        cx = cy = self.width() / 2
        d = 22 + 2 * h + 2 * s
        dot = QRectF(cx - d / 2, cy - d / 2, d, d)

        g = QLinearGradient(dot.left(), dot.top(), dot.right(), dot.bottom())
        g.setColorAt(0.0, QColor(self._c1))
        g.setColorAt(1.0, QColor(self._c2))
        if (s + h) > 0.05:
            halo = QColor(self._c1)
            halo.setAlphaF(min(0.5, (0.22 * s + 0.16 * h) * max(0.4, settings.glow_alpha)))
            p.setPen(Qt.NoPen)
            p.setBrush(halo)
            p.drawEllipse(dot.adjusted(-6, -6, 6, 6))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(g))
        p.drawEllipse(dot)

        if s > 0.01:
            ring = QColor(self._c1)
            ring.setAlphaF(0.9 * s)
            p.setBrush(Qt.NoBrush)
            p.setPen(QPen(ring, 1.8))
            rd = d + 10
            p.drawEllipse(QRectF(cx - rd / 2, cy - rd / 2, rd, rd))
            pm = icons.pixmap("check", 12, "#04121A", 2.6)
            p.setOpacity(s)
            p.drawPixmap(int(cx - 6), int(cy - 6), pm)
            p.setOpacity(1.0)
        p.end()


# ===========================================================================
class LogoOrb(GlowAware, QWidget):
    """Фирменный орб: картинка логотипа с мягким дыханием и ореолом."""

    def __init__(self, size: int = 56, parent=None, breathe: bool = True,
                 asset: str = "logo_512.png"):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._phase = 0.0
        self._breathe = breathe
        self._pm = load_pixmap(cfg.LOGO / asset, int(size * 0.92), int(size * 0.92))
        if breathe:
            driver().subscribe(self, self._tick)

    def _tick(self, dt: float):
        if not settings.get("heavy_effects"):
            return
        self._phase = (self._phase + dt * 0.9) % (math.pi * 2)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        s = min(self.width(), self.height())
        acc = current_accent()
        pulse = 0.5 + 0.5 * math.sin(self._phase) if self._breathe else 0.5

        strength = settings.glow_alpha
        if strength > 0.05:
            g = QRadialGradient(QPointF(s / 2, s / 2), s * (0.48 + 0.06 * pulse))
            c = QColor(acc.primary)
            c.setAlphaF(min(0.42, (0.16 + 0.10 * pulse) * strength))
            g.setColorAt(0.0, c)
            c0 = QColor(acc.primary)
            c0.setAlpha(0)
            g.setColorAt(1.0, c0)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawEllipse(QRectF(0, 0, s, s))

        if not self._pm.isNull():
            scale = 1.0 + 0.012 * pulse if self._breathe else 1.0
            w = self._pm.width() * scale
            h = self._pm.height() * scale
            p.drawPixmap(QRectF((s - w) / 2, (s - h) / 2, w, h), self._pm,
                         QRectF(self._pm.rect()))
        p.end()


# ===========================================================================
class OrbIcon(GlowAware, QWidget):
    """Круглая иконка-орб (готовая картинка) с ореолом и hover-откликом."""

    def __init__(self, name: str, size: int = 48, parent=None, hover: bool = False):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._name = name
        self._hov = Spring(0.0, 20.0)
        self._hoverable = hover
        px = min(256, max(32, int(size * 2)))
        for cand in (256, 128, 96, 64, 48, 32):
            if cand >= px:
                px = cand
                break
        self._pm = load_pixmap(cfg.ORBS / f"{name}_{px}.png", size, size)
        if hover:
            self.setAttribute(Qt.WA_Hover, True)
            driver().subscribe(self, self._tick)

    def enterEvent(self, e):
        if self._hoverable:
            self._hov.set(1.0)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hov.set(0.0)
        super().leaveEvent(e)

    def _tick(self, dt: float):
        if self._hov.done:
            return
        self._hov.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        s = min(self.width(), self.height())
        strength = settings.glow_alpha
        if strength > 0.05:
            acc = current_accent()
            g = QRadialGradient(QPointF(s / 2, s / 2), s * 0.62)
            c = QColor(acc.primary)
            c.setAlphaF(min(0.34, (0.12 + 0.10 * self._hov.value) * strength))
            g.setColorAt(0.0, c)
            c0 = QColor(acc.primary)
            c0.setAlpha(0)
            g.setColorAt(1.0, c0)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(g))
            p.drawEllipse(QRectF(0, 0, s, s))
        if not self._pm.isNull():
            k = 1.0 + 0.05 * self._hov.value
            w = self._pm.width() * k
            h = self._pm.height() * k
            p.drawPixmap(QRectF((s - w) / 2, (s - h) / 2, w, h), self._pm,
                         QRectF(self._pm.rect()))
        p.end()


# ===========================================================================
class RingGauge(GlowAware, QWidget):
    """Кольцевой индикатор с плавным подтягиванием значения."""

    def __init__(self, value: float = 0.0, size: int = 128, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._v = Spring(0.0, 6.0)
        self._v.set(value)
        driver().subscribe(self, self._tick)

    def set_value(self, v: float):
        self._v.set(max(0.0, min(100.0, v)))

    def _tick(self, dt: float):
        if self._v.done:
            return
        self._v.step(dt)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = current_accent()
        side = min(self.width(), self.height())
        pad = 11
        rect = QRectF(pad, pad, side - pad * 2, side - pad * 2)

        p.setPen(QPen(QColor(255, 255, 255, 20), 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 0, 360 * 16)

        grad = QConicalGradient(rect.center(), 90)
        grad.setColorAt(0.0, QColor(acc.primary))
        grad.setColorAt(0.5, QColor(acc.secondary))
        grad.setColorAt(1.0, QColor(acc.primary))
        span = int(-self._v.value / 100.0 * 360 * 16)
        if settings.glow_alpha > 0.05:
            halo = QColor(acc.primary)
            halo.setAlphaF(min(0.35, 0.24 * settings.glow_alpha))
            p.setPen(QPen(halo, 15, Qt.SolidLine, Qt.RoundCap))
            p.drawArc(rect, 90 * 16, span)
        p.setPen(QPen(QBrush(grad), 9, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(rect, 90 * 16, span)

        f = QFont()
        f.setPointSizeF(side * 0.15)
        f.setWeight(QFont.Black)
        p.setFont(f)
        p.setPen(QColor("#EDF3FF"))
        p.drawText(rect, Qt.AlignCenter, f"{int(round(self._v.value))}%")
        p.end()


# ===========================================================================
class HintTip(QWidget):
    """Всплывающая подсказка в стиле программы.

    Показывается рядом с курсором через небольшую задержку, гаснет плавно.
    Используется значками «?» у инструментов.
    """

    _current: "HintTip | None" = None

    def __init__(self, text: str, parent=None):
        super().__init__(parent, Qt.ToolTip | Qt.FramelessWindowHint
                         | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._text = text
        self._pad = 14
        self._max_w = 330
        font = QFont("Inter")
        font.setPixelSize(13)
        self.setFont(font)
        metrics = QFontMetrics(font)
        rect = metrics.boundingRect(
            QRect(0, 0, self._max_w - self._pad * 2, 4000),
            Qt.TextWordWrap, text)
        self._text_rect = rect
        self.resize(min(self._max_w, rect.width() + self._pad * 2),
                    rect.height() + self._pad * 2)
        self._opacity = 0.0
        self.setWindowOpacity(0.0)
        self._fade = QTimer(self)
        self._fade.timeout.connect(self._step)

    @classmethod
    def show_at(cls, text: str, global_pos: QPoint):
        cls.hide_current()
        tip = HintTip(text)
        screen = QGuiApplication.screenAt(global_pos) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
        x = global_pos.x() + 16
        y = global_pos.y() + 18
        if x + tip.width() > area.right() - 8:
            x = global_pos.x() - tip.width() - 12
        if y + tip.height() > area.bottom() - 8:
            y = global_pos.y() - tip.height() - 12
        tip.move(max(area.left() + 4, x), max(area.top() + 4, y))
        tip.show()
        tip._fade.start(16)
        cls._current = tip
        return tip

    @classmethod
    def hide_current(cls):
        if cls._current is not None:
            cls._current.close()
            cls._current.deleteLater()
            cls._current = None

    def _step(self):
        self._opacity = min(1.0, self._opacity + 0.16)
        self.setWindowOpacity(self._opacity)
        if self._opacity >= 1.0:
            self._fade.stop()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 11, 11)
        p.fillPath(path, QColor(16, 19, 27, 250))
        edge = QColor(current_accent().primary)
        edge.setAlpha(90)
        p.setPen(QPen(edge, 1.0))
        p.drawPath(path)
        p.setPen(QColor("#DCE3F0"))
        p.drawText(self.rect().adjusted(self._pad, self._pad,
                                        -self._pad, -self._pad),
                   Qt.TextWordWrap | Qt.AlignLeft | Qt.AlignVCenter,
                   self._text)
        p.end()


class HelpDot(GlowAware, QWidget):
    """Значок «?»: при наведении объясняет, для чего нужен инструмент."""

    def __init__(self, text: str, size: int = 20, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._text = text
        self._hover = Spring(0.0, 22.0)
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.WhatsThisCursor)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._popup)
        driver().subscribe(self, self._tick)

    def _tick(self, dt: float):
        if self._hover.done:
            return
        self._hover.step(dt)
        self.update()

    def enterEvent(self, e):
        self._hover.set(1.0)
        self._timer.start(320)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover.set(0.0)
        self._timer.stop()
        HintTip.hide_current()
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._popup()
        super().mousePressEvent(e)

    def _popup(self):
        if self.isVisible():
            HintTip.show_at(self._text, self.mapToGlobal(
                QPoint(self.width() // 2, self.height())))

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = current_accent()
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        k = self._hover.value
        fill = QColor(acc.primary)
        fill.setAlphaF(0.10 + 0.24 * k)
        p.setBrush(QBrush(fill))
        pen = QColor(acc.primary)
        pen.setAlphaF(0.45 + 0.4 * k)
        p.setPen(QPen(pen, 1.2))
        p.drawEllipse(r)
        f = QFont("Inter")
        f.setPixelSize(max(11, int(self.height() * 0.62)))
        f.setBold(True)
        p.setFont(f)
        col = QColor("#EAF2FF")
        col.setAlphaF(0.72 + 0.28 * k)
        p.setPen(col)
        p.drawText(self.rect(), Qt.AlignCenter, "?")
        p.end()
