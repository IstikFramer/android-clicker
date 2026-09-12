"""Fast recursive file search page and background worker."""

from __future__ import annotations

import fnmatch
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from PySide6.QtCore import QDate, QObject, QThread, Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugins.file_manager.styles import TEXTS as T
from plugins.file_manager.utils import (
    FileManagerConfig,
    format_datetime,
    format_size,
    icon_for_path,
    is_probably_text,
    open_with_system,
    parse_extensions,
    safe_file_info,
    send_to_trash,
)

LOGGER = logging.getLogger(__name__)


class SearchWorker(QObject):
    """Search filesystem entries without blocking the Qt event loop."""

    found = Signal(object)
    progress = Signal(int, int)
    status = Signal(str)
    error = Signal(str)
    finished = Signal(int, float)

    def __init__(self, options: dict[str, Any]) -> None:
        """Store immutable search options."""
        super().__init__()
        self.options = options

    @Slot()
    def run(self) -> None:
        """Walk the selected directory and emit matching entries."""
        started = time.monotonic()
        count = 0
        visited = 0
        try:
            root = Path(self.options["root"])
            max_results = int(self.options.get("max_results", 10000))
            nodes = self._iter_nodes(root, bool(self.options.get("recursive", True)))
            for node in nodes:
                if QThread.currentThread().isInterruptionRequested():
                    break
                visited += 1
                if visited % 25 == 0:
                    self.progress.emit(visited, max(visited + 1, 100))
                if self._matches(node):
                    info = safe_file_info(node)
                    if info is None and node.is_file():
                        continue
                    stat = node.stat()
                    result = {
                        "path": str(node),
                        "name": node.name,
                        "size": stat.st_size if node.is_file() else 0,
                        "modified": stat.st_mtime,
                        "is_dir": node.is_dir(),
                    }
                    self.found.emit(result)
                    count += 1
                    if count >= max_results:
                        break
            self.finished.emit(count, time.monotonic() - started)
        except (PermissionError, FileNotFoundError, OSError, ValueError) as error:
            self.error.emit(str(error))
            self.finished.emit(count, time.monotonic() - started)

    def _iter_nodes(self, root: Path, recursive: bool) -> Iterator[Path]:
        """Yield files or folders according to the selected result type."""
        try:
            with os.scandir(root) as entries:
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        yield path
                        if entry.is_dir(follow_symlinks=False) and recursive:
                            yield from self._iter_nodes(path, True)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
            return

    def _matches(self, path: Path) -> bool:
        """Apply name, type, extension, size, date and content filters."""
        query = str(self.options.get("query", "")).strip().casefold()
        if query and not (query in path.name.casefold() or fnmatch.fnmatch(path.name.casefold(), query)):
            return False
        result_type = self.options.get("result_type", "all")
        if result_type == "files" and not path.is_file():
            return False
        if result_type == "folders" and not path.is_dir():
            return False
        extensions = self.options.get("extensions", set())
        if extensions and path.is_file() and path.suffix.casefold() not in extensions:
            return False
        if extensions and path.is_dir():
            return False
        if path.is_file():
            try:
                size = path.stat().st_size
            except (PermissionError, FileNotFoundError, OSError):
                return False
            if not self.options["min_bytes"] <= size <= self.options["max_bytes"]:
                return False
            modified = datetime.fromtimestamp(path.stat().st_mtime).date()
            if not self.options["date_from"] <= modified <= self.options["date_to"]:
                return False
            content = str(self.options.get("content", "")).strip()
            if self.options.get("search_content") and content:
                if not is_probably_text(path) or not self._contains_text(path, content):
                    return False
        return True

    @staticmethod
    def _contains_text(path: Path, text: str) -> bool:
        """Look for a text fragment in a bounded text-file read."""
        try:
            with path.open("r", encoding="utf-8", errors="ignore") as source:
                for line in source:
                    if text.casefold() in line.casefold():
                        return True
        except (PermissionError, FileNotFoundError, OSError, UnicodeError):
            return False
        return False


class FileSearchPage(QWidget):
    """Interactive file and folder search page."""

    status_message = Signal(str)
    progress_changed = Signal(int, int)
    busy_changed = Signal(bool)
    cancel_requested = Signal()

    def __init__(self, config: FileManagerConfig, parent: QWidget | None = None) -> None:
        """Create search controls and restore the last selected folder."""
        super().__init__(parent)
        self.config = config
        self._thread: QThread | None = None
        self._worker: SearchWorker | None = None
        self._started = 0.0
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the search form and results table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        title = QLabel(T["search"], self)
        title.setProperty("fmRole", "section")
        layout.addWidget(title)

        query_row = QHBoxLayout()
        self.query_edit = QLineEdit(self)
        self.query_edit.setPlaceholderText("Имя файла или шаблон *.txt")
        self.query_edit.returnPressed.connect(self.start_search)
        query_row.addWidget(self.query_edit, 1)
        search_button = QPushButton(T["search_button"], self)
        search_button.setProperty("fmRole", "primary")
        search_button.clicked.connect(self.start_search)
        query_row.addWidget(search_button)
        layout.addLayout(query_row)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(self.config.get("last_paths.search", ""), self)
        self.folder_edit.setPlaceholderText(T["folder_placeholder"])
        folder_row.addWidget(self.folder_edit, 1)
        browse = QPushButton(T["browse"], self)
        browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        filters = QFrame(self)
        filters.setProperty("fmRole", "group")
        filter_layout = QVBoxLayout(filters)
        filter_layout.setContentsMargins(10, 8, 10, 8)
        filter_layout.setSpacing(7)
        self.filter_button = QPushButton(T["filter_panel"], filters)
        self.filter_button.setProperty("fmRole", "nav")
        self.filter_button.clicked.connect(lambda: self.filter_controls.setVisible(not self.filter_controls.isVisible()))
        filter_layout.addWidget(self.filter_button)
        self.filter_controls = QWidget(filters)
        controls = QVBoxLayout(self.filter_controls)
        controls.setContentsMargins(0, 0, 0, 0)
        type_row = QHBoxLayout()
        self.type_combo = QComboBox(self.filter_controls)
        self.type_combo.addItem(T["all"], "all")
        self.type_combo.addItem(T["files_only"], "files")
        self.type_combo.addItem(T["folders_only"], "folders")
        type_row.addWidget(QLabel(T["file_type"], self.filter_controls))
        type_row.addWidget(self.type_combo)
        self.extension_edit = QLineEdit(self.filter_controls)
        self.extension_edit.setPlaceholderText(".py .txt")
        type_row.addWidget(QLabel(T["extension"], self.filter_controls))
        type_row.addWidget(self.extension_edit, 1)
        self.recursive_check = QCheckBox(T["include_subfolders"], self.filter_controls)
        self.recursive_check.setChecked(True)
        type_row.addWidget(self.recursive_check)
        controls.addLayout(type_row)

        size_row = QHBoxLayout()
        self.min_size = QDoubleSpinBox(self.filter_controls)
        self.min_size.setRange(0, 999999999)
        self.max_size = QDoubleSpinBox(self.filter_controls)
        self.max_size.setRange(0, 999999999)
        self.max_size.setValue(999999999)
        self.unit_combo = QComboBox(self.filter_controls)
        for unit in ("KB", "MB", "GB"):
            self.unit_combo.addItem(unit, unit)
        size_row.addWidget(QLabel(T["min_size"], self.filter_controls))
        size_row.addWidget(self.min_size)
        size_row.addWidget(QLabel(T["max_size"], self.filter_controls))
        size_row.addWidget(self.max_size)
        size_row.addWidget(self.unit_combo)
        controls.addLayout(size_row)

        date_row = QHBoxLayout()
        self.date_from = QDateEdit(self.filter_controls)
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate(1970, 1, 1))
        self.date_to = QDateEdit(self.filter_controls)
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate().addDays(1))
        date_row.addWidget(QLabel(T["date_from"], self.filter_controls))
        date_row.addWidget(self.date_from)
        date_row.addWidget(QLabel(T["date_to"], self.filter_controls))
        date_row.addWidget(self.date_to)
        controls.addLayout(date_row)

        content_row = QHBoxLayout()
        self.content_check = QCheckBox(T["content_search"], self.filter_controls)
        self.content_edit = QLineEdit(self.filter_controls)
        self.content_edit.setPlaceholderText(T["content_text"])
        self.content_edit.setEnabled(False)
        self.content_check.toggled.connect(self.content_edit.setEnabled)
        content_row.addWidget(self.content_check)
        content_row.addWidget(self.content_edit, 1)
        controls.addLayout(content_row)
        filter_layout.addWidget(self.filter_controls)
        self.filter_controls.setVisible(False)
        layout.addWidget(filters)

        self.results = QTableWidget(0, 5, self)
        self.results.setHorizontalHeaderLabels(["", T["file_name"], T["file_path"], T["file_size"], T["modified"]])
        self.results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.results.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results.customContextMenuRequested.connect(self.show_context_menu)
        self.results.cellDoubleClicked.connect(self.open_selected)
        self.results.horizontalHeader().setStretchLastSection(True)
        self.results.setColumnWidth(0, 36)
        self.results.setColumnWidth(1, 190)
        self.results.setColumnWidth(2, 360)
        layout.addWidget(self.results, 1)
        self.result_status = QLabel(T["ready"], self)
        self.result_status.setProperty("fmRole", "muted")
        layout.addWidget(self.result_status)

    def choose_folder(self) -> None:
        """Let the user choose the search root."""
        selected = QFileDialog.getExistingDirectory(self, T["select_folder"], self.folder_edit.text())
        if selected:
            self.folder_edit.setText(selected)
            self.config.set("last_paths.search", selected)

    def _options(self) -> dict[str, Any]:
        """Collect current filter values for a worker."""
        unit = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}[self.unit_combo.currentData() or "KB"]
        return {
            "root": self.folder_edit.text().strip(),
            "query": self.query_edit.text(),
            "result_type": self.type_combo.currentData() or "all",
            "extensions": parse_extensions(self.extension_edit.text()),
            "min_bytes": int(self.min_size.value() * unit),
            "max_bytes": int(self.max_size.value() * unit),
            "recursive": self.recursive_check.isChecked(),
            "date_from": self.date_from.date().toPython(),
            "date_to": self.date_to.date().toPython(),
            "search_content": self.content_check.isChecked(),
            "content": self.content_edit.text(),
            "max_results": int(self.config.get("search.max_results", 10000)),
        }

    def start_search(self) -> None:
        """Start a background search using the current filters."""
        root = Path(self.folder_edit.text().strip())
        if not root.is_dir():
            self.status_message.emit(T["select_folder"])
            return
        self.config.set("last_paths.search", str(root))
        self.results.setRowCount(0)
        self._started = time.monotonic()
        self._thread = QThread(self)
        self._worker = SearchWorker(self._options())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.found.connect(self.add_result)
        self._worker.progress.connect(self.progress_changed)
        self._worker.error.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()
        self.busy_changed.emit(True)
        self.cancel_requested.connect(self.cancel_search)
        self.status_message.emit(T["search_button"])

    @Slot(object)
    def add_result(self, result: dict[str, Any]) -> None:
        """Append one worker result to the table."""
        row = self.results.rowCount()
        self.results.insertRow(row)
        path = Path(result["path"])
        icon = QTableWidgetItem()
        icon.setIcon(icon_for_path(path))
        name = QTableWidgetItem(result["name"])
        name.setData(Qt.ItemDataRole.UserRole, result["path"])
        self.results.setItem(row, 0, icon)
        self.results.setItem(row, 1, name)
        self.results.setItem(row, 2, QTableWidgetItem(result["path"]))
        self.results.setItem(row, 3, QTableWidgetItem(format_size(result["size"])))
        self.results.setItem(row, 4, QTableWidgetItem(format_datetime(result["modified"])))

    def _on_error(self, message: str) -> None:
        """Show a worker error in the page status."""
        LOGGER.warning("File search failed: %s", message)
        self.status_message.emit(f"{T['status_error']}: {message}")

    def _on_finished(self, count: int, elapsed: float) -> None:
        """Finish the operation and show the result count."""
        self.busy_changed.emit(False)
        self.result_status.setText(T["found"].format(count=count, seconds=elapsed))
        self.status_message.emit(self.result_status.text())
        try:
            self.cancel_requested.disconnect(self.cancel_search)
        except (RuntimeError, TypeError):
            pass

    def cancel_search(self) -> None:
        """Request cancellation of the current worker."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.requestInterruption()
            self.status_message.emit(T["cancel"])

    def open_selected(self, row: int, column: int) -> None:
        """Open the selected result with its system application."""
        item = self.results.item(row, 1)
        if item is None:
            return
        try:
            open_with_system(Path(str(item.data(Qt.ItemDataRole.UserRole))))
        except (OSError, RuntimeError) as error:
            self.status_message.emit(f"{T['status_error']}: {error}")

    def _selected_path(self) -> Path | None:
        """Return the path in the current table row."""
        row = self.results.currentRow()
        if row < 0 or self.results.item(row, 1) is None:
            return None
        return Path(str(self.results.item(row, 1).data(Qt.ItemDataRole.UserRole)))

    def show_context_menu(self, position: Any) -> None:
        """Show safe file actions for the selected result."""
        path = self._selected_path()
        if path is None:
            return
        menu = QMenu(self)
        open_action = QAction(T["open"], menu)
        folder_action = QAction(T["open_folder"], menu)
        copy_action = QAction(T["copy_path"], menu)
        delete_action = QAction(T["delete_trash"], menu)
        menu.addAction(open_action)
        menu.addAction(folder_action)
        menu.addAction(copy_action)
        menu.addSeparator()
        menu.addAction(delete_action)
        open_action.triggered.connect(lambda: self._open_path(path))
        folder_action.triggered.connect(lambda: self._open_path(path.parent))
        copy_action.triggered.connect(lambda: self._copy_path(path))
        delete_action.triggered.connect(lambda: self._delete_path(path))
        menu.exec(self.results.viewport().mapToGlobal(position))

    def _open_path(self, path: Path) -> None:
        """Open a path and report operating system errors."""
        try:
            open_with_system(path)
        except (OSError, RuntimeError) as error:
            self.status_message.emit(f"{T['status_error']}: {error}")

    def _copy_path(self, path: Path) -> None:
        """Copy a selected path to the clipboard."""
        self.window().windowHandle()
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(str(path))
        self.status_message.emit(T["copy_path"])

    def _delete_path(self, path: Path) -> None:
        """Confirm and move a selected result to the trash."""
        answer = QMessageBox.question(self, T["delete_trash"], f"Удалить в корзину?\n{path}")
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            send_to_trash(path)
            row = self.results.currentRow()
            if row >= 0:
                self.results.removeRow(row)
            self.status_message.emit(T["delete_trash"])
        except (OSError, RuntimeError) as error:
            self.status_message.emit(f"{T['status_error']}: {error}")
