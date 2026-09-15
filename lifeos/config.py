"""LIFE OS — глобальные константы и пути."""
from __future__ import annotations

from pathlib import Path

APP_NAME = "LIFE OS"
APP_TAGLINE = "Персональная операционная система"
APP_VERSION = "0.1"
APP_BUILD = "0.1.0-alpha"
APP_ORG = "IstikFramer"

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGO = ASSETS / "logo"
ICONS = ASSETS / "icons"
BACKGROUNDS = ASSETS / "backgrounds"
FONTS = ASSETS / "fonts"

# Геометрия окна
WINDOW_MIN_W, WINDOW_MIN_H = 1100, 700
WINDOW_DEF_W, WINDOW_DEF_H = 1360, 840
WINDOW_RADIUS = 18
TITLEBAR_H = 52
SIDEBAR_W = 264
SIDEBAR_W_COLLAPSED = 76
RESIZE_MARGIN = 6


def asset(*parts: str) -> str:
    """Путь к ассету строкой (для QSS нужен posix-вид)."""
    return (ASSETS.joinpath(*parts)).as_posix()
