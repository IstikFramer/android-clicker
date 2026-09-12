"""Dynamic discovery and loading of application plugins."""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QWidget

from core.signals import app_signals
from core.utils import get_app_dir


class PluginLoader:
    """Find valid plugin packages in the application's ``plugins`` folder."""

    REQUIRED_INFO_KEYS = ("name", "version", "description", "author", "widget_class")

    def __init__(self, plugins_dir: Path | str | None = None) -> None:
        """Initialize a loader for a plugin directory."""
        self._logger = logging.getLogger(__name__)
        self.plugins_dir = Path(plugins_dir) if plugins_dir else get_app_dir() / "plugins"
        self.plugins: list[dict[str, Any]] = []

    def load_plugins(self) -> list[dict[str, Any]]:
        """Scan, import and instantiate all valid plugins.

        Returns:
            Plugin dictionaries containing metadata and a ``widget`` instance.
            A broken plugin is logged and skipped without stopping the shell.
        """
        self.plugins = []
        if not self.plugins_dir.exists():
            self._logger.info("Plugin directory does not exist: %s", self.plugins_dir)
            return self.plugins
        try:
            directories = sorted(self.plugins_dir.iterdir(), key=lambda path: path.name.lower())
        except OSError as error:
            self._logger.exception("Could not scan plugin directory: %s", error)
            return self.plugins

        for plugin_path in directories:
            if not plugin_path.is_dir() or plugin_path.name.startswith("_"):
                continue
            if not (plugin_path / "__init__.py").exists():
                self._logger.warning("Skipped %s: __init__.py is missing", plugin_path)
                continue
            loaded = self._load_one(plugin_path)
            if loaded is not None:
                self.plugins.append(loaded)
                app_signals.plugin_loaded.emit(dict(loaded))
        self._logger.info("Loaded %d plugin(s)", len(self.plugins))
        return list(self.plugins)

    def _load_one(self, plugin_path: Path) -> dict[str, Any] | None:
        """Import and validate one plugin package."""
        module_name = f"plugins.{plugin_path.name}"
        try:
            module = importlib.import_module(module_name)
            info = getattr(module, "PLUGIN_INFO", None)
            if not isinstance(info, dict):
                raise ValueError("PLUGIN_INFO must be a dictionary")
            missing = [key for key in self.REQUIRED_INFO_KEYS if key not in info]
            if missing:
                raise ValueError(f"PLUGIN_INFO missing keys: {', '.join(missing)}")
            class_name = str(info["widget_class"])
            widget_class = getattr(module, class_name, None)
            if not isinstance(widget_class, type) or not issubclass(widget_class, QWidget):
                raise TypeError(f"{class_name} must be a QWidget subclass")
            widget = widget_class()
            metadata: dict[str, Any] = dict(info)
            metadata.update(
                {
                    "module_name": module_name,
                    "path": str(plugin_path),
                    "widget": widget,
                }
            )
            return metadata
        except Exception as error:  # noqa: BLE001 - plugin failures are isolated by design
            self._logger.exception("Could not load plugin %s: %s", module_name, error)
            return None

    def reload_plugins(self) -> list[dict[str, Any]]:
        """Reload already imported plugin modules and scan again."""
        for plugin in self.plugins:
            module_name = plugin.get("module_name")
            if isinstance(module_name, str):
                try:
                    module = importlib.import_module(module_name)
                    importlib.reload(module)
                except Exception as error:  # noqa: BLE001 - a plugin must not crash the shell
                    self._logger.warning("Could not reload plugin %s: %s", module_name, error)
        return self.load_plugins()
