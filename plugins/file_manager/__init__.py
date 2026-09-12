"""File management plugin entry point."""

from __future__ import annotations

PLUGIN_INFO = {
    "name": "Файловый менеджмент",
    "version": "0.1.5",
    "description": "Сортировка, поиск, дубликаты, переименование и анализ диска",
    "author": "dev",
    "icon": "folder.svg",
    "widget_class": "FileManagerWidget",
}

from plugins.file_manager.widget import FileManagerWidget

__all__ = ["PLUGIN_INFO", "FileManagerWidget"]
