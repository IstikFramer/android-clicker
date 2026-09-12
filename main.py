"""Entry point for the Shell desktop application."""

from __future__ import annotations

import logging
import sys
import traceback
from types import TracebackType
from typing import Type

from PySide6.QtWidgets import QApplication, QMessageBox

from core.app import APP_NAME, ShellApplication, configure_logging
from core.config import ConfigManager
from core.main_window import MainWindow


def handle_exception(
    exception_type: Type[BaseException],
    exception_value: BaseException,
    exception_traceback: TracebackType | None,
) -> None:
    """Log an uncaught exception and show a user-facing error dialog."""
    if issubclass(exception_type, KeyboardInterrupt):
        sys.__excepthook__(exception_type, exception_value, exception_traceback)
        return
    logging.getLogger(__name__).critical(
        "Unhandled application exception",
        exc_info=(exception_type, exception_value, exception_traceback),
    )
    application = QApplication.instance()
    if application is not None:
        try:
            QMessageBox.critical(
                None,
                "Ошибка приложения",
                f"{APP_NAME} столкнулся с неожиданной ошибкой.\n\n"
                f"Подробности записаны в data/app.log.\n"
                f"{exception_value}",
            )
        except Exception:  # noqa: BLE001 - the fallback must never mask the original error
            traceback.print_exception(exception_type, exception_value, exception_traceback)


def main() -> int:
    """Configure and run the application event loop."""
    configure_logging()
    sys.excepthook = handle_exception
    config = ConfigManager()
    panel_opacity = config.get("effects.panel_opacity", 80)
    try:
        panel_opacity = max(50, min(100, int(panel_opacity)))
    except (TypeError, ValueError):
        panel_opacity = 80
    application = ShellApplication(sys.argv, panel_opacity=panel_opacity)
    window = MainWindow(config)
    if bool(config.get("general.start_minimized", False)):
        window.showMinimized()
    else:
        window.show()
    logging.getLogger(__name__).info("%s v%s started", APP_NAME, application.applicationVersion())
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
