"""LIFE OS — глобальные константы и пути."""
from __future__ import annotations

from pathlib import Path

APP_NAME = "LIFE OS"
APP_TAGLINE = "Персональная операционная система"
APP_VERSION = "0.2"
APP_BUILD = "0.2.0-alpha"
APP_CHANNEL = "ALPHA"

DEV_NAME = "IKOOF inc."
DEV_EMAIL = "IKOOF1298W@gmail.com"
DEV_YEAR = "2026"

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
LOGO = ASSETS / "logo"
ORBS = ASSETS / "orbs"
BACKGROUNDS = ASSETS / "backgrounds"
DATA = ROOT / "data"
USER_DIR = Path.home() / ".lifeos"
SETTINGS_FILE = USER_DIR / "settings.json"
BACKUP_DIR = USER_DIR / "backups"

# Геометрия окна
WINDOW_MIN_W, WINDOW_MIN_H = 1060, 680
WINDOW_DEF_W, WINDOW_DEF_H = 1340, 840
WINDOW_RADIUS = 18
TITLEBAR_H = 54
SIDEBAR_W = 252
SIDEBAR_W_COLLAPSED = 74
RESIZE_MARGIN = 6
