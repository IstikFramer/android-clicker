"""Frameless main window, navigation shell and system tray integration."""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QAction, QMouseEvent, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QStatusBar,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

try:
    from qframelesswindow import FramelessMainWindow as _FramelessMainWindow

    FRAMELESS_WINDOW_AVAILABLE = True
except Exception:  # noqa: BLE001 - the native helper is optional on unsupported systems
    _FramelessMainWindow = QMainWindow
    FRAMELESS_WINDOW_AVAILABLE = False

from core.app import APP_NAME, APP_VERSION
from core.config import ConfigManager
from core.home_page import HomePage
from core.plugin_loader import PluginLoader
from core.settings_page import SettingsPage
from core.sidebar import Sidebar
from core.theme import Sizes
from core.utils import load_icon


class TitleBar(QWidget):
    """Custom title bar with window controls and drag support."""

    close_requested = Signal()
    minimize_requested = Signal()
    maximize_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create a title bar attached to a top-level window."""
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(Sizes.TITLE_BAR_HEIGHT)
        self._drag_position: QPoint | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build title bar labels and controls."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 0, 0)
        layout.setSpacing(8)

        icon_label = QLabel(self)
        icon_label.setPixmap(load_icon("app_icon.svg").pixmap(16, 16))
        icon_label.setFixedSize(16, 16)
        layout.addWidget(icon_label)

        title = QLabel(APP_NAME, self)
        title.setObjectName("windowTitle")
        layout.addWidget(title)
        layout.addStretch(1)

        self.minimize_button = self._make_button("minimize.svg", "Свернуть", "title-button")
        self.maximize_button = self._make_button("maximize.svg", "Развернуть", "title-button")
        self.close_button = self._make_button("close.svg", "Закрыть", "close-button")
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

        self.minimize_button.clicked.connect(self.minimize_requested.emit)
        self.maximize_button.clicked.connect(self.maximize_requested.emit)
        self.close_button.clicked.connect(self.close_requested.emit)

    @staticmethod
    def _make_button(icon_name: str, tooltip: str, role: str) -> QPushButton:
        """Create a title-bar icon button."""
        button = QPushButton()
        button.setIcon(load_icon(icon_name))
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)
        button.setProperty("role", role)
        return button

    def update_maximize_icon(self, maximized: bool) -> None:
        """Update the maximize tooltip after a window state change."""
        self.maximize_button.setToolTip("Восстановить" if maximized else "Развернуть")

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Start moving the parent window on a left-button press."""
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.window()
            if window.isMaximized():
                self._drag_position = None
            else:
                self._drag_position = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Move the parent window while the title bar is held."""
        if self._drag_position is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Finish a title-bar drag."""
        self._drag_position = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """Toggle maximized state on a title-bar double click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.maximize_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)


class MainWindow(_FramelessMainWindow):
    """Main Fluent window with native Mica or Acrylic background effects."""

    def __init__(self, config: ConfigManager | None = None) -> None:
        """Create the window, restore state and load available plugins."""
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.config = config or ConfigManager()
        self._resize_edge: str | None = None
        self._resize_start_geometry = QRect()
        self._resize_start_position = QPoint()
        self._size_grip: QSizeGrip | None = None
        self._restore_maximized = False
        self._force_close = False
        self._effect_applied = False
        self._active_effect = "none"
        self.tray_icon: QSystemTrayIcon | None = None
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 550)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if not FRAMELESS_WINDOW_AVAILABLE:
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self._build_shell()
        self._restore_geometry()
        self._connect_signals()
        self._setup_tray()
        self._load_plugins()
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)

    def _build_shell(self) -> None:
        """Build the title bar, navigation area, page stack and status bar."""
        frame = QFrame(self)
        frame.setObjectName("windowFrame")
        frame.setMouseTracking(True)
        root_layout = QVBoxLayout(frame)
        root_layout.setSpacing(0)

        self.title_bar = TitleBar(self if FRAMELESS_WINDOW_AVAILABLE else frame)
        self.title_bar.close_requested.connect(self.close)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_requested.connect(self.toggle_maximized)
        if FRAMELESS_WINDOW_AVAILABLE and hasattr(self, "setTitleBar"):
            self.setTitleBar(self.title_bar)
            root_layout.setContentsMargins(1, Sizes.TITLE_BAR_HEIGHT + 1, 1, 1)
        else:
            root_layout.setContentsMargins(1, 1, 1, 1)
            root_layout.addWidget(self.title_bar)

        body = QWidget(frame)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        self.sidebar = Sidebar(self.config, body)
        self.content_stack = QStackedWidget(body)
        self.content_stack.setObjectName("contentStack")
        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.content_stack, 1)
        root_layout.addWidget(body, 1)

        self._size_grip = QSizeGrip(frame)
        self._size_grip.setFixedSize(16, 16)
        self.setCentralWidget(frame)
        self._setup_status_bar()

        self.home_page = HomePage(open_plugin=self.navigate_to)
        self.settings_page = SettingsPage(self.config)
        self.add_page(self.home_page)
        self.add_page(self.settings_page)
        self.sidebar.add_navigation_item("Главная", "home.svg", 0)
        self.sidebar.add_navigation_item("Настройки", "settings.svg", 1)
        self.content_stack.setCurrentIndex(0)
        self.sidebar.set_active_page(0)

    def _setup_status_bar(self) -> None:
        """Create the compact application status bar."""
        status_bar = QStatusBar(self)
        status_bar.setFixedHeight(Sizes.STATUS_BAR_HEIGHT)
        status_label = QLabel("Готово", status_bar)
        status_label.setObjectName("statusMessage")
        version_label = QLabel(f"v{APP_VERSION}", status_bar)
        version_label.setObjectName("statusVersion")
        version_label.setProperty("role", "muted")
        status_bar.addWidget(status_label)
        status_bar.addPermanentWidget(version_label)
        self.setStatusBar(status_bar)
        self.status_label = status_label

    def _connect_signals(self) -> None:
        """Connect page, sidebar and global application signals."""
        from core.signals import app_signals

        self.sidebar.navigation_requested.connect(self.navigate_to)
        self.settings_page.status_message.connect(self.set_status)
        app_signals.navigate_to.connect(self.navigate_to)
        app_signals.status_message.connect(self.set_status)

    def _setup_tray(self) -> None:
        """Create the tray icon and its context menu when supported."""
        application = QApplication.instance()
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._logger.info("System tray is not available")
            if application is not None:
                application.setQuitOnLastWindowClosed(True)
            return
        if application is not None:
            application.setQuitOnLastWindowClosed(False)
        self.tray_icon = QSystemTrayIcon(load_icon("app_icon.svg"), self)
        self.tray_icon.setToolTip(APP_NAME)
        menu = QMenu(self)
        show_action = QAction("Развернуть", self)
        settings_action = QAction("Настройки", self)
        quit_action = QAction("Выход", self)
        show_action.triggered.connect(self.show_window)
        settings_action.triggered.connect(self.show_settings_from_tray)
        quit_action.triggered.connect(self.quit_from_tray)
        menu.addAction(show_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Show the window on a tray click or double click."""
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.show_window()

    def show_window(self) -> None:
        """Restore and focus the main window from the tray."""
        self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    def show_settings_from_tray(self) -> None:
        """Show the window and open the settings page from the tray."""
        self.show_window()
        self.navigate_to(1)

    def quit_from_tray(self) -> None:
        """Close the application explicitly from the tray menu."""
        self._force_close = True
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.close()
        application = QApplication.instance()
        if application is not None:
            application.quit()

    def _load_plugins(self) -> None:
        """Load plugin pages and add their navigation entries."""
        loader = PluginLoader()
        for plugin in loader.load_plugins():
            widget = plugin.get("widget")
            if not isinstance(widget, QWidget):
                continue
            page_index = self.add_page(widget)
            plugin["page_index"] = page_index
            icon_name = str(plugin.get("icon", "about.svg"))
            if not icon_name.endswith(".svg"):
                icon_name = "about.svg"
            self.sidebar.add_navigation_item(str(plugin.get("name", "Модуль")), icon_name, page_index)
        self.home_page.set_modules(loader.plugins)

    def add_page(self, page: QWidget) -> int:
        """Add a page to the central stack and return its index."""
        return self.content_stack.addWidget(page)

    def navigate_to(self, page_index: int) -> None:
        """Switch to a valid page index and update navigation state."""
        if not 0 <= page_index < self.content_stack.count():
            self._logger.warning("Ignored invalid page index: %s", page_index)
            return
        self.content_stack.setCurrentIndex(page_index)
        self.sidebar.set_active_page(page_index)
        if page_index == 0:
            self.set_status("Главная")
        elif page_index == 1:
            self.set_status("Настройки")
        else:
            self.set_status("Модуль открыт")

    def set_status(self, message: str) -> None:
        """Display a short message in the status bar."""
        self.status_label.setText(message)

    def toggle_maximized(self) -> None:
        """Toggle between the normal and maximized window states."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        self.title_bar.update_maximize_icon(self.isMaximized())

    def _restore_geometry(self) -> None:
        """Restore a valid saved geometry or center the default size."""
        window = self.config.get_section("window")
        try:
            width = max(900, int(window.get("width", 1200)))
        except (TypeError, ValueError):
            width = 1200
        try:
            height = max(550, int(window.get("height", 750)))
        except (TypeError, ValueError):
            height = 750
        self.resize(width, height)
        x, y = window.get("x"), window.get("y")
        if isinstance(x, int) and isinstance(y, int) and self._point_is_visible(x, y):
            self.move(x, y)
        else:
            self._center_on_screen()
        self._restore_maximized = bool(window.get("maximized", False))

    @staticmethod
    def _point_is_visible(x: int, y: int) -> bool:
        """Return whether a saved top-left point is on a connected screen."""
        for screen in QApplication.screens():
            if screen.availableGeometry().adjusted(-40, -40, 40, 40).contains(x, y):
                return True
        return False

    def _center_on_screen(self) -> None:
        """Center the window on the primary available screen."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        available = screen.availableGeometry()
        self.move(available.center() - self.rect().center())

    def showEvent(self, event: Any) -> None:
        """Apply saved maximized state and the selected backdrop."""
        super().showEvent(event)
        if not self._effect_applied:
            self.apply_window_effect(str(self.config.get("effects.window_effect", "mica")))
        if self._restore_maximized:
            self.showMaximized()
            self.title_bar.update_maximize_icon(True)
            self._restore_maximized = False

    def apply_window_effect(self, effect_name: str) -> str:
        """Apply Mica, Acrylic or a solid fallback without raising.

        Args:
            effect_name: ``mica``, ``acrylic`` or ``none``.

        Returns:
            The effect that is active after capability detection.
        """
        requested = effect_name.strip().lower()
        if requested not in {"mica", "acrylic", "none"}:
            requested = "mica"
        active = "none"
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, requested != "none")
        try:
            effect = getattr(self, "windowEffect", None)
            if requested == "none":
                if effect is not None and hasattr(effect, "removeBackgroundEffect"):
                    effect.removeBackgroundEffect(self.winId())
            elif effect is not None and sys.platform == "win32":
                if requested == "mica" and self._supports_mica():
                    effect.setMicaEffect(self.winId(), isDarkMode=True)
                    active = "mica"
                else:
                    effect.setAcrylicEffect(self.winId())
                    active = "acrylic"
            elif requested != "none":
                # qframelesswindow keeps this method as a safe no-op on Linux.
                if effect is not None and hasattr(effect, "setAcrylicEffect"):
                    effect.setAcrylicEffect(self.winId())
                active = requested
        except Exception as error:  # noqa: BLE001 - visual effects are optional
            self._logger.warning("Window effect %s was unavailable: %s", requested, error)
            active = self._apply_blur_fallback(requested)
        self._active_effect = active
        self._effect_applied = True
        self.setProperty("windowEffect", active)
        self._refresh_style(self)
        self._logger.info("Window backdrop: requested=%s active=%s", requested, active)
        return active

    def _apply_blur_fallback(self, requested: str) -> str:
        """Try BlurWindow on Windows, then retain the QSS glass fallback."""
        if requested == "none":
            return "none"
        if sys.platform == "win32":
            try:
                from BlurWindow.blurWindow import GlobalBlur

                GlobalBlur(self.winId(), "#1a1a2eB8", Acrylic=requested == "acrylic", Dark=True)
                return requested
            except Exception as error:  # noqa: BLE001 - fallback is best effort
                self._logger.warning("BlurWindow fallback was unavailable: %s", error)
        return "qss"

    @staticmethod
    def _supports_mica() -> bool:
        """Return whether the current Windows build is expected to support Mica."""
        if sys.platform != "win32":
            return False
        try:
            build = int(getattr(sys, "getwindowsversion")().build)
            return build >= 22000 and bool(platform.version())
        except (AttributeError, OSError, TypeError, ValueError):
            return False

    @staticmethod
    def _refresh_style(widget: QWidget) -> None:
        """Re-evaluate dynamic effect properties after a backdrop change."""
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Keep the manual resize grip in the bottom-right corner."""
        super().resizeEvent(event)
        if self._size_grip is not None and self.centralWidget() is not None:
            frame = self.centralWidget()
            self._size_grip.move(frame.width() - self._size_grip.width(), frame.height() - self._size_grip.height())

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        """Provide edge resize behavior for a frameless window."""
        del watched
        if FRAMELESS_WINDOW_AVAILABLE or self.isMaximized() or not self.isVisible():
            return False
        event_type = event.type()
        if event_type == QEvent.Type.MouseButtonPress:
            if isinstance(event, QMouseEvent) and event.button() == Qt.MouseButton.LeftButton:
                global_position = event.globalPosition().toPoint()
                self._resize_edge = self._edge_at(global_position)
                if self._resize_edge:
                    self._resize_start_geometry = self.geometry()
                    self._resize_start_position = global_position
        elif event_type == QEvent.Type.MouseMove:
            if isinstance(event, QMouseEvent):
                global_position = event.globalPosition().toPoint()
                if self._resize_edge and event.buttons() & Qt.MouseButton.LeftButton:
                    self._resize_to(global_position)
                elif not event.buttons():
                    self._update_edge_cursor(global_position)
        elif event_type == QEvent.Type.MouseButtonRelease:
            self._resize_edge = None
            self.unsetCursor()
        return False

    def _edge_at(self, global_position: QPoint) -> str | None:
        """Find a resize edge near a global cursor position."""
        local = self.mapFromGlobal(global_position)
        margin = 6
        if local.y() <= Sizes.TITLE_BAR_HEIGHT:
            return None
        left = local.x() <= margin
        right = local.x() >= self.width() - margin
        top = local.y() <= margin
        bottom = local.y() >= self.height() - margin
        if top and left:
            return "top-left"
        if top and right:
            return "top-right"
        if bottom and left:
            return "bottom-left"
        if bottom and right:
            return "bottom-right"
        if left:
            return "left"
        if right:
            return "right"
        if top:
            return "top"
        if bottom:
            return "bottom"
        return None

    def _update_edge_cursor(self, global_position: QPoint) -> None:
        """Set an appropriate cursor for an available resize edge."""
        edge = self._edge_at(global_position)
        cursors = {
            "left": Qt.CursorShape.SizeHorCursor,
            "right": Qt.CursorShape.SizeHorCursor,
            "top": Qt.CursorShape.SizeVerCursor,
            "bottom": Qt.CursorShape.SizeVerCursor,
            "top-left": Qt.CursorShape.SizeFDiagCursor,
            "bottom-right": Qt.CursorShape.SizeFDiagCursor,
            "top-right": Qt.CursorShape.SizeBDiagCursor,
            "bottom-left": Qt.CursorShape.SizeBDiagCursor,
        }
        if edge in cursors:
            self.setCursor(cursors[edge])
        else:
            self.unsetCursor()

    def _resize_to(self, global_position: QPoint) -> None:
        """Resize from the active edge while respecting the minimum size."""
        delta = global_position - self._resize_start_position
        geometry = QRect(self._resize_start_geometry)
        edge = self._resize_edge or ""
        if "left" in edge:
            geometry.setLeft(min(geometry.left() + delta.x(), geometry.right() - self.minimumWidth() + 1))
        if "right" in edge:
            geometry.setRight(max(geometry.right() + delta.x(), geometry.left() + self.minimumWidth() - 1))
        if "top" in edge:
            geometry.setTop(min(geometry.top() + delta.y(), geometry.bottom() - self.minimumHeight() + 1))
        if "bottom" in edge:
            geometry.setBottom(max(geometry.bottom() + delta.y(), geometry.top() + self.minimumHeight() - 1))
        self.setGeometry(geometry)

    def closeEvent(self, event: Any) -> None:
        """Save geometry or minimize to the tray according to preferences."""
        tray_on_close = bool(self.config.get("general.tray_on_close", True))
        if self.tray_icon is not None and tray_on_close and not self._force_close:
            self._save_geometry()
            self.hide()
            self.tray_icon.show()
            event.ignore()
            return
        self._save_geometry()
        if self.tray_icon is not None:
            self.tray_icon.hide()
        application = QApplication.instance()
        if application is not None:
            application.removeEventFilter(self)
        super().closeEvent(event)

    def _save_geometry(self) -> None:
        """Persist position, size and maximized state."""
        maximized = self.isMaximized()
        self.config.set("window.maximized", maximized)
        if not maximized:
            geometry = self.geometry()
            self.config.set("window.width", geometry.width())
            self.config.set("window.height", geometry.height())
            self.config.set("window.x", geometry.x())
            self.config.set("window.y", geometry.y())
