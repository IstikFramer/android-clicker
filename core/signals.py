"""Signals shared by application components."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    """Central signal hub for navigation and lightweight status updates."""

    status_message = Signal(str)
    navigate_to = Signal(int)
    theme_changed = Signal(str)
    plugin_loaded = Signal(dict)


app_signals = AppSignals()
"