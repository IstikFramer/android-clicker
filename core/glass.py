"""Reusable animated glass surfaces for the desktop shell."""

from __future__ import annotations

import math

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QWidget

from core.theme import shadow_color


def _with_alpha(color_name: str, alpha: int) -> QColor:
    """Return a color with a clamped alpha channel."""
    color = QColor(color_name)
    color.setAlpha(max(0, min(255, alpha)))
    return color


def paint_ambient_background(
    painter: QPainter,
    rect: QRectF,
    phase: float = 0.0,
    transparent_base: bool = False,
) -> None:
    """Paint a subtle animated ambient background behind translucent surfaces.

    The background is deliberately rendered by Qt instead of relying on a
    platform-specific blur API. It therefore remains attractive on Linux,
    Windows fallback mode, virtual machines and remote desktop sessions. When
    a native Mica or Acrylic material is active, ``transparent_base`` keeps
    the platform backdrop visible and paints only the animated light layer.
    """
    if rect.width() <= 0 or rect.height() <= 0:
        return
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setClipRect(rect)

    if not transparent_base:
        base = QLinearGradient(rect.topLeft(), rect.bottomRight())
        base.setColorAt(0.0, QColor("#11182d"))
        base.setColorAt(0.48, QColor("#101a35"))
        base.setColorAt(1.0, QColor("#091224"))
        painter.fillRect(rect, base)

    width = rect.width()
    height = rect.height()
    angle = phase * math.pi / 180.0
    blobs = (
        (0.18 + math.sin(angle * 0.70) * 0.07, 0.12 + math.cos(angle * 0.55) * 0.05, 0.56, "#00adb5"),
        (0.82 + math.cos(angle * 0.48) * 0.06, 0.28 + math.sin(angle * 0.63) * 0.08, 0.62, "#0f3460"),
        (0.48 + math.sin(angle * 0.38) * 0.10, 0.94 + math.cos(angle * 0.44) * 0.04, 0.72, "#1d4d78"),
    )
    for x, y, radius, color_name in blobs:
        point_x = rect.left() + width * x
        point_y = rect.top() + height * y
        gradient = QRadialGradient(point_x, point_y, max(width, height) * radius)
        gradient.setColorAt(0.0, _with_alpha(color_name, 72))
        gradient.setColorAt(0.42, _with_alpha(color_name, 24))
        gradient.setColorAt(1.0, _with_alpha(color_name, 0))
        painter.fillRect(rect, gradient)

    # A quiet grid and top highlight provide depth without looking like noise.
    grid_pen = QPen(_with_alpha("#9eeff2", 10), 1)
    painter.setPen(grid_pen)
    step = 42
    start_x = int(rect.left()) - int(rect.left()) % step
    start_y = int(rect.top()) - int(rect.top()) % step
    for x in range(start_x, int(rect.right()) + step, step):
        painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
    for y in range(start_y, int(rect.bottom()) + step, step):
        painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    highlight = QLinearGradient(rect.topLeft(), rect.topRight())
    highlight.setColorAt(0.0, _with_alpha("#ffffff", 18))
    highlight.setColorAt(0.35, _with_alpha("#ffffff", 5))
    highlight.setColorAt(1.0, _with_alpha("#ffffff", 0))
    painter.fillRect(QRectF(rect.left(), rect.top(), width, 1.0), highlight)
    painter.restore()


class GlassBackdrop(QFrame):
    """Animated, platform-independent glass backdrop for the shell."""

    def __init__(self, parent: QWidget | None = None, animated: bool = True) -> None:
        """Create the backdrop and start a low-cost ambient animation."""
        super().__init__(parent)
        self._phase = 0.0
        self._native_material = False
        self.setObjectName("windowFrame")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._timer = QTimer(self)
        self._timer.setInterval(42)
        self._timer.timeout.connect(self._advance)
        if animated:
            self._timer.start()

    def set_animated(self, animated: bool) -> None:
        """Enable or disable the ambient movement."""
        if animated:
            self._timer.start()
        else:
            self._timer.stop()

    def set_native_material(self, active: bool) -> None:
        """Keep a native Mica or Acrylic backdrop visible below the lights."""
        self._native_material = active
        self.update()

    def _advance(self) -> None:
        """Advance the ambient phase and repaint the backdrop."""
        self._phase = (self._phase + 0.65) % 360.0
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the gradient, ambient lights and a thin glass border."""
        del event
        painter = QPainter(self)
        paint_ambient_background(
            painter,
            QRectF(self.rect()),
            self._phase,
            transparent_base=self._native_material,
        )
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        border_path = QPainterPath()
        border_path.addRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 12.0, 12.0)
        painter.setPen(QPen(_with_alpha("#d8ffff", 42), 1.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(border_path)
        painter.end()


class GlassCard(QFrame):
    """Glass card with a shadow, hover glow and subtle animated highlight."""

    def __init__(self, parent: QWidget | None = None, frame_role: str = "card") -> None:
        """Create a translucent card."""
        super().__init__(parent)
        self.setProperty("frameRole", frame_role)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._hovered = False
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(30)
        self._shadow.setOffset(0, 3)
        self._shadow.setColor(shadow_color())
        self.setGraphicsEffect(self._shadow)
        self._shadow_animation: QPropertyAnimation | None = None

    def enterEvent(self, event: QEvent) -> None:
        """Increase the shadow softly when the pointer enters the card."""
        self._hovered = True
        self._animate_shadow(38)
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Return the shadow to its resting intensity."""
        self._hovered = False
        self._animate_shadow(30)
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event: object) -> None:
        """Draw a translucent tonal surface and a fine highlight border."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        radius = 12.0 if self.property("frameRole") == "large-card" else 9.0
        surface = QLinearGradient(0, 0, 0, self.height())
        surface.setColorAt(0.0, _with_alpha("#ffffff", 28 if self._hovered else 20))
        surface.setColorAt(0.45, _with_alpha("#9eeff2", 12 if self._hovered else 8))
        surface.setColorAt(1.0, _with_alpha("#061127", 54))
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()).adjusted(1.0, 1.0, -1.0, -1.0), radius, radius)
        painter.fillPath(path, surface)
        painter.setPen(QPen(_with_alpha("#d8ffff", 62 if self._hovered else 34), 1.0))
        painter.drawPath(path)
        painter.setPen(QPen(_with_alpha("#ffffff", 18), 1.0))
        painter.drawLine(int(radius), 1, max(int(radius), self.width() - int(radius)), 1)
        painter.end()

    def _animate_shadow(self, target_blur: int) -> None:
        """Animate the card shadow blur without blocking the UI."""
        if self._shadow_animation is not None:
            self._shadow_animation.stop()
        animation = QPropertyAnimation(self._shadow, b"blurRadius", self)
        animation.setDuration(150)
        animation.setStartValue(self._shadow.blurRadius())
        animation.setEndValue(target_blur)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._shadow_animation = animation
        animation.start()
