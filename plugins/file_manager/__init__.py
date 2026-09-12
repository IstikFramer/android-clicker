"""File management plugin entry point."""

from __future__ import annotations

from plugins.file_manager.styles import TEXTS as T

PLUGIN_INFO = {
    "name": T["plugin_name"],
    "version": "0.1.5",
    "description": T["plugin_description"],
    "author": "dev",
    "icon": "folder.svg",
    "widget_class": "FileManagerWidget",
}

from plugins.file_manager.widget import FileManagerWidget

__all__ = ["PLUGIN_INFO", "FileManagerWidget"]
