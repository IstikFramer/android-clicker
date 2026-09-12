"""Root widget for the file management plugin."""

from __future__ import annotations

import logging

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, QTimer, Qt, Signal
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.glass import paint_ambient_background
from core.utils import load_icon
from plugins.file_manager.styles import TEXTS as T, stylesheet
from plugins.file_manager.utils import FileManagerConfig


class FileManagerWidget(QWidget):
    """Main file management workspace with five submodule pages."""

    status_message = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the workspace and its navigation shell."""
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.config = FileManagerConfig()
        self._page_animation: QPropertyAnimation | None = None
        self._nav_buttons: list[QPushButton] = []
        self._ambient_phase = 0.0
        self.setObjectName("fileManagerRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(stylesheet())
        self._ambient_timer = QTimer(self)
        self._ambient_timer.setInterval(42)
        self._ambient_timer.timeout.connect(self._advance_ambient)
        self._ambient_timer.start()
        self._build_ui()

    def _advance_ambient(self) -> None:
        """Move the ambient light behind the module surfaces."""
        self._ambient_phase = (self._ambient_phase + 0.65) % 360.0
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the module background before its translucent panels."""
        del event
        painter = QPainter(self)
        paint_ambient_background(painter, QRectF(self.rect()), self._ambient_phase)
        painter.end()

    def _build_ui(self) -> None:
        """Build header, navigation, page stack and operation status area."""
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 14)
        root.setSpacing(12)
        root.addWidget(self._create_header())

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)
        self.sidebar = self._create_sidebar()
        self.stack = QStackedWidget(self)
        self.stack.setObjectName("fileManagerStack")
        body.addWidget(self.sidebar)
        body.addWidget(self.stack, 1)
        root.addLayout(body, 1)

        self.status_frame, self.status_label, self.progress_bar, self.cancel_button = self._create_status_bar()
        root.addWidget(self.status_frame)
        self._build_pages()

    def _create_header(self) -> QFrame:
        """Create the module title and short description."""
        header = QFrame(self)
        header.setProperty("fmRole", "header")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(4, 0, 4, 8)
        layout.setSpacing(2)
        title = QLabel(T["title"], header)
        title.setProperty("fmRole", "title")
        description = QLabel(T["description"], header)
        description.setProperty("fmRole", "subtitle")
        layout.addWidget(title)
        layout.addWidget(description)
        return header

    def _create_sidebar(self) -> QFrame:
        """Create the vertical submodule navigation."""
        sidebar = QFrame(self)
        sidebar.setProperty("fmRole", "sidebar")
        sidebar.setMinimumWidth(164)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 10, 8, 10)
        layout.setSpacing(4)
        items = (
            (T["sort"], "sort.svg"),
            (T["duplicates"], "duplicate.svg"),
            (T["rename"], "rename.svg"),
            (T["space"], "disk.svg"),
            (T["search"], "search.svg"),
        )
        for index, (label, icon_name) in enumerate(items):
            button = QPushButton(label, sidebar)
            button.setProperty("fmRole", "nav")
            button.setProperty("active", index == 0)
            button.setIcon(load_icon(icon_name))
            button.setIconSize(QSize(18, 18))
            button.setToolTip(label)
            button.clicked.connect(lambda checked=False, value=index: self.switch_page(value))
            self._nav_buttons.append(button)
            layout.addWidget(button)
        layout.addStretch(1)
        return sidebar

    def _create_status_bar(self) -> tuple[QFrame, QLabel, QProgressBar, QPushButton]:
        """Create the status and progress controls shared by submodules."""
        frame = QFrame(self)
        frame.setProperty("fmRole", "panel")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)
        label = QLabel(T["ready"], frame)
        label.setProperty("fmRole", "muted")
        progress = QProgressBar(frame)
        progress.setRange(0, 100)
        progress.setValue(0)
        progress.setVisible(False)
        cancel = QPushButton(T["cancel"], frame)
        cancel.setProperty("fmRole", "danger")
        cancel.setVisible(False)
        layout.addWidget(label, 1)
        layout.addWidget(progress, 0)
        layout.addWidget(cancel, 0)
        return frame, label, progress, cancel

    def _build_pages(self) -> None:
        """Create and connect all concrete file management pages."""
        from plugins.file_manager.bulk_rename import BulkRenamePage
        from plugins.file_manager.duplicate_finder import DuplicateFinderPage
        from plugins.file_manager.file_search import FileSearchPage
        from plugins.file_manager.smart_organizer import SmartOrganizerPage
        from plugins.file_manager.space_analyzer import SpaceAnalyzerPage

        pages = (
            SmartOrganizerPage(self.config, self),
            DuplicateFinderPage(self.config, self),
            BulkRenamePage(self.config, self),
            SpaceAnalyzerPage(self.config, self),
            FileSearchPage(self.config, self),
        )
        for index, page in enumerate(pages):
            self.add_page(page, index)
            self.connect_page(page)

    def add_page(self, page: QWidget, index: int | None = None) -> int:
        """Insert a concrete tool page into the stack.

        Args:
            page: Widget implementing one file management tool.
            index: Optional placeholder index to replace.

        Returns:
            The page index in the stack.
        """
        if index is not None and 0 <= index < self.stack.count():
            old_page = self.stack.widget(index)
            self.stack.removeWidget(old_page)
            old_page.deleteLater()
            self.stack.insertWidget(index, page)
            return index
        return self.stack.addWidget(page)

    def connect_page(self, page: QWidget) -> None:
        """Connect common signals exposed by a tool page."""
        status = getattr(page, "status_message", None)
        if status is not None:
            status.connect(self.set_status)
        progress = getattr(page, "progress_changed", None)
        if progress is not None:
            progress.connect(self.set_progress)
        busy = getattr(page, "busy_changed", None)
        if busy is not None:
            busy.connect(self.set_busy)
        cancel_operation = getattr(page, "cancel_operation", None)
        if cancel_operation is not None:
            self.cancel_button.clicked.connect(cancel_operation)

    def switch_page(self, index: int) -> None:
        """Switch to a submodule page with a short fade transition."""
        if not 0 <= index < self.stack.count() or index == self.stack.currentIndex():
            return
        self.stack.setCurrentIndex(index)
        for position, button in enumerate(self._nav_buttons):
            button.setProperty("active", position == index)
            self._refresh_style(button)
        if self._page_animation is not None:
            self._page_animation.stop()
        page = self.stack.currentWidget()
        effect = QGraphicsOpacityEffect(page)
        effect.setOpacity(0.0)
        page.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(150)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: page.setGraphicsEffect(None))
        self._page_animation = animation
        animation.start()

    def set_status(self, message: str) -> None:
        """Set the shared operation status message."""
        self.status_label.setText(message)
        self.status_message.emit(message)

    def set_progress(self, current: int, total: int) -> None:
        """Update the shared progress bar."""
        if total <= 0:
            self.progress_bar.setVisible(False)
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(max(0, min(100, int(current * 100 / total))))

    def set_busy(self, busy: bool) -> None:
        """Show or hide progress and cancellation controls."""
        self.cancel_button.setVisible(busy)
        if not busy:
            self.progress_bar.setVisible(False)
            self.progress_bar.setValue(0)

    def cancel_current(self) -> None:
        """Request cancellation from the active page."""
        self.set_status(T["cancel"])

    @staticmethod
    def _refresh_style(widget: QWidget) -> None:
        """Refresh a dynamic navigation property."""
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()
