"""Frameless main window and its reusable title bar."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QMouseEvent, QResizeEvent
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizeGrip,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.app import APP_NAME, APP_VERSION
from core.config import ConfigManager
from core.theme import Colors, Sizes
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
        self.close_button = self._make_button("close.svg", "Закрыть", "title-button close-button")
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

        self.minimize_button.clicked.connect(self.minimize_requested.emit)
        self.maximize_button.clicked.connect(self.maximize_requested.emit)
        self.close_button.clicked.connect(self.close_requested.emit)

    @staticmethod
    def _make_button(icon_name: str, tooltip: str, roles: str) -> QPushButton:
        """Create a title-bar icon button."""
        button = QPushButton()
        button.setIcon(load_icon(icon_name))
        button.setIconSize(QSize(16, 16))
        button.setToolTip(tooltip)
        button.setProperty("role", roles)
        if "close-button" in roles:
            button.setProperty("role", "close-button")
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


class MainWindow(QMainWindow):
    """Main frameless window used by the Shell application.

    The window owns the title bar, central stacked content area and status bar.
    Feature pages can be added through :meth:`add_page`.
    """

    def __init__(self, config: ConfigManager | None = None) -> None:
        """Create the window and restore its previous geometry."""
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.config = config or ConfigManager()
        self._resize_edge: str | None = None
        self._resize_start_geometry = QRect()
        self._resize_start_position = QPoint()
        self._size_grip: QSizeGrip | None = None
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(900, 550)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._build_shell()
        self._restore_geometry()
        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)

    def _build_shell(self) -> None:
        """Build the frame, title bar, content stack and status bar."""
        frame = QFrame(self)
        frame.setObjectName("windowFrame")
        frame.setMouseTracking(True)
        root_layout = QVBoxLayout(frame)
        root_layout.setContentsMargins(1, 1, 1, 1)
        root_layout.setSpacing(0)

        self.title_bar = TitleBar(frame)
        self.title_bar.close_requested.connect(self.close)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_requested.connect(self.toggle_maximized)
        root_layout.addWidget(self.title_bar)

        self.content_stack = QStackedWidget(frame)
        self.content_stack.setObjectName("contentStack")
        root_layout.addWidget(self.content_stack, 1)

        self._size_grip = QSizeGrip(frame)
        self._size_grip.setFixedSize(16, 16)

        self.setCentralWidget(frame)
        self._setup_status_bar()

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

    def add_page(self, page: QWidget) -> int:
        """Add a page to the central stack and return its index."""
        return self.content_stack.addWidget(page)

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
        width = max(900, int(window.get("width", 1200)))
        height = max(550, int(window.get("height", 750)))
        self.resize(width, height)
        x, y = window.get("x"), window.get("y")
        if isinstance(x, int) and isinstance(y, int) and self._point_is_visible(x, y):
            self.move(x, y)
        else:
            self._center_on_screen()
        if bool(window.get("maximized", False)):
            self._restore_maximized = True
        else:
            self._restore_maximized = False

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
        """Apply saved maximized state after the native window exists."""
        super().showEvent(event)
        if getattr(self, "_restore_maximized", False):
            self.showMaximized()
            self.title_bar.update_maximize_icon(True)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Keep the manual resize grip in the bottom-right corner."""
        super().resizeEvent(event)
        if self._size_grip is not None and self.centralWidget() is not None:
            frame = self.centralWidget()
            self._size_grip.move(frame.width() - self._size_grip.width(), frame.height() - self._size_grip.height())

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """Provide edge resize behavior for a frameless window."""
        del watched
        if self.isMaximized() or not self.isVisible():
            return False
        event_type = event.type()
        if event_type == QEvent.Type.MouseButtonPress:
            mouse_event = event
            if isinstance(mouse_event, QMouseEvent) and mouse_event.button() == Qt.MouseButton.LeftButton:
                global_position = mouse_event.globalPosition().toPoint()
                self._resize_edge = self._edge_at(global_position)
                if self._resize_edge:
                    self._resize_start_geometry = self.geometry()
                    self._resize_start_position = global_position
                    return False
        elif event_type == QEvent.Type.MouseMove:
            mouse_event = event
            if isinstance(mouse_event, QMouseEvent):
                global_position = mouse_event.globalPosition().toPoint()
                if self._resize_edge and mouse_event.buttons() & Qt.MouseButton.LeftButton:
                    self._resize_to(global_position)
                    return False
                if not mouse_event.buttons():
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
        """Save normal geometry before the window is destroyed."""
        self._save_geometry()
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


# Imported only for the type annotation in eventFilter on older PySide versions.
from PySide6.QtCore import QObject  # noqa: E402
