"""Reusable animated glass card surface."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, Qt
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QWidget

from core.theme import shadow_color


class GlassCard(QFrame):
    """QFrame with a glass surface, shadow and animated hover glow."""

    def __init__(self, parent: QWidget | None = None, frame_role: str = "card") -> None:
        """Create a glass card.

        Args:
            parent: Optional parent widget.
            frame_role: QSS role, normally ``card`` or ``large-card``.
        """
        super().__init__(parent)
        self.setProperty("frameRole", frame_role)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(30)
        self._shadow.setOffset(0, 3)
        self._shadow.setColor(shadow_color())
        self.setGraphicsEffect(self._shadow)
        self._shadow_animation: QPropertyAnimation | None = None

    def enterEvent(self, event: QEvent) -> None:
        """Increase the shadow softly when the pointer enters the card."""
        self._animate_shadow(38)
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Return the shadow to its resting intensity."""
        self._animate_shadow(30)
        super().leaveEvent(event)

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
