"""Persistent, thread-safe application configuration."""

from __future__ import annotations

import copy
import json
import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import QMutex


class ConfigManager:
    """Read and persist user settings in a JSON file.

    Args:
        path: Optional path to the configuration file. The application data
            location is used when omitted.
    """

    DEFAULTS: dict[str, dict[str, Any]] = {
        "window": {
            "width": 1200,
            "height": 750,
            "x": None,
            "y": None,
            "maximized": False,
        },
        "general": {
            "autostart": False,
            "tray_on_close": True,
            "start_minimized": False,
            "language": "ru",
        },
        "appearance": {
            "theme": "dark",
            "scale": 100,
            "animations": True,
        },
        "effects": {
            "window_effect": "mica",
            "panel_opacity": 80,
        },
        "updates": {
            "check_on_start": True,
        },
        "sidebar": {
            "collapsed": False,
        },
    }

    def __init__(self, path: Path | str | None = None) -> None:
        """Initialize the manager and load the existing configuration."""
        self._logger = logging.getLogger(__name__)
        self._mutex = QMutex()
        self.path = Path(path) if path else Path(__file__).resolve().parents[1] / "data" / "config.json"
        self._data: dict[str, Any] = copy.deepcopy(self.DEFAULTS)
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """Return a setting, optionally using dotted section syntax.

        Args:
            key: Setting name such as ``general.tray_on_close``.
            default: Value returned when the setting does not exist.

        Returns:
            The stored value or ``default``.
        """
        current: Any = self._data
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return copy.deepcopy(current)

    def set(self, key: str, value: Any) -> None:
        """Set a setting and immediately save it to disk.

        Args:
            key: Setting name such as ``appearance.scale``.
            value: JSON-serializable value.
        """
        parts = key.split(".")
        if not all(parts):
            self._logger.warning("Ignored invalid configuration key: %s", key)
            return
        current = self._data
        for part in parts[:-1]:
            child = current.get(part)
            if not isinstance(child, dict):
                child = {}
                current[part] = child
            current = child
        current[parts[-1]] = copy.deepcopy(value)
        self._save()

    def get_section(self, section_name: str) -> dict[str, Any]:
        """Return a copy of a complete configuration section."""
        section = self._data.get(section_name, {})
        return copy.deepcopy(section) if isinstance(section, dict) else {}

    def reset(self) -> None:
        """Restore defaults and persist them."""
        self._data = copy.deepcopy(self.DEFAULTS)
        self._save()

    def _load(self) -> None:
        """Load JSON, retaining defaults for missing or invalid values."""
        try:
            if not self.path.exists():
                self._save()
                return
            with self.path.open("r", encoding="utf-8") as config_file:
                loaded = json.load(config_file)
            if isinstance(loaded, dict):
                self._merge(self._data, loaded)
            else:
                self._logger.warning("Configuration root is not an object; defaults used")
        except (OSError, json.JSONDecodeError, TypeError) as error:
            self._logger.exception("Could not load configuration: %s", error)

    def _save(self) -> None:
        """Write the current data atomically while holding the Qt mutex."""
        self._mutex.lock()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary_path = self.path.with_suffix(".json.tmp")
            with temporary_path.open("w", encoding="utf-8") as config_file:
                json.dump(self._data, config_file, ensure_ascii=False, indent=2)
                config_file.write("\n")
            os.replace(temporary_path, self.path)
        except (OSError, TypeError, ValueError) as error:
            self._logger.exception("Could not save configuration: %s", error)
        finally:
            self._mutex.unlock()

    @staticmethod
    def _merge(target: dict[str, Any], source: dict[str, Any]) -> None:
        """Merge a JSON object into defaults without accepting unknown roots."""
        for key, value in source.items():
            if key not in target:
                continue
            if isinstance(target[key], dict) and isinstance(value, dict):
                ConfigManager._merge(target[key], value)
            else:
                target[key] = value
