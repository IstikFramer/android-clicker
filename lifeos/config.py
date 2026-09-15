"""LIFE OS — глобальные константы и пути."""
from __future__ import annotations

import sys
from pathlib import Path

APP_NAME = "LIFE OS"
APP_TAGLINE = "Персональная операционная система"
APP_VERSION = "0.3.5"
APP_BUILD = "0.3.5-alpha"
APP_CHANNEL = "ALPHA"

DEV_NAME = "IKOOF inc."
DEV_EMAIL = "IKOOF1298W@gmail.com"
DEV_YEAR = "2026"

# В собранной программе ресурсы лежат в папке _internal рядом с EXE
# (PyInstaller сообщает путь через sys._MEIPASS), а пользовательские
# файлы — рядом с самим исполняемым файлом.
FROZEN = bool(getattr(sys, "frozen", False))
if FROZEN:
    RES_ROOT = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    ROOT = Path(sys.executable).resolve().parent
else:
    RES_ROOT = Path(__file__).resolve().parents[1]
    ROOT = RES_ROOT

ASSETS = RES_ROOT / "assets"
LOGO = ASSETS / "logo"
ORBS = ASSETS / "orbs"
BACKGROUNDS = ASSETS / "backgrounds"
ICONS = ASSETS / "icons"
DATA = RES_ROOT / "data"
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
