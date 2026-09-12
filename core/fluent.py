"""Optional Fluent Widgets integration with safe Qt fallbacks."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QCheckBox, QComboBox, QPushButton, QScrollArea, QSlider

FLUENT_AVAILABLE = False

try:
    from qfluentwidgets import (  # type: ignore[import-not-found]
        CheckBox,
        ComboBox,
        PrimaryPushButton,
        PushButton,
        Slider,
        SmoothScrollArea,
        ToggleButton,
        TransparentPushButton,
        Theme,
        setTheme,
        setThemeColor,
    )

    FLUENT_AVAILABLE = True
except Exception:  # noqa: BLE001 - Fluent Widgets is an optional enhancement
    CheckBox = QCheckBox
    ComboBox = QComboBox
    PrimaryPushButton = QPushButton
    PushButton = QPushButton
    Slider = QSlider
    SmoothScrollArea = QScrollArea
    ToggleButton = QPushButton
    TransparentPushButton = QPushButton
    Theme = None

    def setTheme(*args: Any, **kwargs: Any) -> None:
        """Fallback for the optional Fluent theme function."""

    def setThemeColor(*args: Any, **kwargs: Any) -> None:
        """Fallback for the optional Fluent accent function."""


def configure_fluent(accent: str) -> None:
    """Configure qfluentwidgets when it is installed and importable.

    Args:
        accent: Accent color in a format accepted by qfluentwidgets.
    """
    if not FLUENT_AVAILABLE or Theme is None:
        return
    try:
        setTheme(Theme.DARK)
        setThemeColor(accent)
    except Exception:  # noqa: BLE001 - optional styling must never block startup
        return
