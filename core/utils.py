"""Small cross-platform helpers used throughout the application."""

from __future__ import annotations

import getpass
import logging
import os
import platform
import sys
from pathlib import Path

try:
    import darkdetect
except ImportError:  # pragma: no cover - dependency is installed in normal use
    darkdetect = None  # type: ignore[assignment]

from PySide6.QtGui import QIcon


LOGGER = logging.getLogger(__name__)


def format_bytes(size: int | float) -> str:
    """Format a byte count with a compact binary unit.

    Args:
        size: Number of bytes.

    Returns:
        A human-readable value such as ``1.5 GB``.
    """
    try:
        value = float(size)
    except (TypeError, ValueError):
        return "0 B"
    if value < 0:
        value = 0
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    unit_index = 0
    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1
    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    return f"{value:.1f} {units[unit_index]}"


def get_user_name() -> str:
    """Return the current operating-system user name safely."""
    try:
        name = getpass.getuser().strip()
        return name or "Пользователь"
    except (OSError, KeyError):
        return "Пользователь"


def get_app_dir() -> Path:
    """Return the application root for source and frozen deployments."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def get_data_dir() -> Path:
    """Return the writable data directory and create it if needed."""
    path = get_app_dir() / "data"
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        LOGGER.error("Could not create data directory %s: %s", path, error)
    return path


def resource_path(relative: str) -> Path:
    """Resolve an asset path for source and PyInstaller deployments.

    Args:
        relative: Path relative to the project root or bundled resources.

    Returns:
        The resolved resource path.
    """
    base_path = Path(getattr(sys, "_MEIPASS", get_app_dir()))
    return base_path / relative


def icon_path(name: str) -> Path:
    """Return the path to an icon in the bundled icon directory."""
    return resource_path(f"assets/icons/{name}")


def load_icon(name: str) -> QIcon:
    """Load an application icon without raising when a resource is missing."""
    path = icon_path(name)
    if not path.exists():
        LOGGER.warning("Icon resource does not exist: %s", path)
        return QIcon()
    return QIcon(os.fspath(path))


def is_system_dark() -> bool:
    """Return the system dark-mode preference with a safe default."""
    if darkdetect is None:
        return True
    try:
        return bool(darkdetect.isDark())
    except Exception:  # noqa: BLE001 - platform theme detection is optional
        return True


def supports_mica() -> bool:
    """Return whether the current host is expected to support Windows 11 Mica."""
    if sys.platform != "win32":
        return False
    try:
        build = int(getattr(sys, "getwindowsversion")().build)
        return build >= 22000 and bool(platform.version())
    except (AttributeError, OSError, TypeError, ValueError):
        return False
