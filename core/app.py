"""Application constants and QApplication wrapper."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.theme import application_font, generate_stylesheet
from core.utils import get_data_dir, load_icon

APP_NAME = "Shell"
APP_VERSION = "0.1"
APP_DEVELOPER = "Разработчик"


class ShellApplication(QApplication):
    """Configure Qt for the Shell desktop application."""

    def __init__(self, arguments: list[str]) -> None:
        """Create the application and apply the shared visual language."""
        super().__init__(arguments)
        self.setApplicationName(APP_NAME)
        self.setApplicationDisplayName(APP_NAME)
        self.setApplicationVersion(APP_VERSION)
        self.setWindowIcon(load_icon("app_icon.svg"))
        self.setFont(application_font())
        self.setStyleSheet(generate_stylesheet())


def configure_logging(data_dir: Path | None = None) -> None:
    """Configure rotating file and console logging for the application.

    Args:
        data_dir: Optional directory for ``app.log``. The normal data path is
            used when omitted.
    """
    directory = data_dir or get_data_dir()
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        directory = Path.cwd()
    log_path = directory / "app.log"
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return
    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
