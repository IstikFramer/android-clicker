"""Duplicate file finder with staged hashing and safe delete actions."""

from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from plugins.file_manager.styles import TEXTS as T
from plugins.file_manager.utils import (
    FileManagerConfig,
    format_datetime,
    format_size,
    hash_file,
    iter_files,
    send_to_trash,
)

LOGGER = logging.getLogger(__name__)


class DuplicateWorker(QObject):
    """Find duplicate files with size, partial and full hash stages."""

    phase = Signal(str)
    progress = Signal(int, int)
    groups_found = Signal(object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, root: Path, minimum_size: int, recursive: bool) -> None:
        """Store duplicate scan options."""
        super().__init__()
        self.root = root
        self.minimum_size = minimum_size
        self.recursive = recursive

    @Slot()
    def run(self) -> None:
        """Run the three-stage duplicate algorithm."""
        try:
            self.phase.emit("Этап 1/3: Анализ размеров...")
            by_size: dict[int, list[Path]] = defaultdict(list)
            files = list(iter_files(self.root, self.recursive))
            for index, path in enumerate(files, 1):
                if QThread.currentThread().isInterruptionRequested():
                    self.finished.emit()
                    return
                try:
                    size = path.stat().st_size
                    if size >= self.minimum_size:
                        by_size[size].append(path)
                except (PermissionError, FileNotFoundError, OSError):
                    continue
                self.progress.emit(index, max(1, len(files)))

            candidates = [group for group in by_size.values() if len(group) > 1]
            self.phase.emit("Этап 2/3: Сравнение первых 4 КБ...")
            partial_groups: list[list[Path]] = []
            for index, group in enumerate(candidates, 1):
                by_partial: dict[str, list[Path]] = defaultdict(list)
                for path in group:
                    digest = hash_file(path, partial=True)
                    if digest is not None:
                        by_partial[digest].append(path)
                partial_groups.extend(values for values in by_partial.values() if len(values) > 1)
                self.progress.emit(index, max(1, len(candidates)))

            self.phase.emit("Этап 3/3: Полное сравнение файлов...")
            duplicate_groups: list[list[str]] = []
            for index, group in enumerate(partial_groups, 1):
                by_full: dict[str, list[str]] = defaultdict(list)
                for path in group:
                    digest = hash_file(path)
                    if digest is not None:
                        by_full[digest].append(str(path))
                duplicate_groups.extend(values for values in by_full.values() if len(values) > 1)
                self.progress.emit(index, max(1, len(partial_groups)))
            self.groups_found.emit(duplicate_groups)
        except (PermissionError, FileNotFoundError, OSError, ValueError) as error:
            self.error.emit(str(error))
        finally:
            self.finished.emit()


class DuplicateFinderPage(QWidget):
    """Page for reviewing and removing groups of duplicate files."""

    status_message = Signal(str)
    progress_changed = Signal(int, int)
    busy_changed = Signal(bool)
    cancel_requested = Signal()

    def __init__(self, config: FileManagerConfig, parent: QWidget | None = None) -> None:
        """Create duplicate finder controls."""
        super().__init__(parent)
        self.config = config
        self._thread: QThread | None = None
        self._worker: DuplicateWorker | None = None
        self._checks: list[tuple[QCheckBox, Path, bool]] = []
        self._groups: list[list[str]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        """Build scan controls and the scrollable result list."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)
        title = QLabel(T["duplicates"], self)
        title.setProperty("fmRole", "section")
        layout.addWidget(title)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(self.config.get("last_paths.duplicates", ""), self)
        self.folder_edit.setPlaceholderText(T["folder_placeholder"])
        folder_row.addWidget(self.folder_edit, 1)
        browse = QPushButton(T["browse"], self)
        browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        options = QHBoxLayout()
        self.minimum_size = QDoubleSpinBox(self)
        self.minimum_size.setRange(0, 999999999)
        self.minimum_size.setValue(1)
        self.minimum_size.setSuffix(" KB")
        self.recursive_check = QCheckBox(T["include_subfolders"], self)
        self.recursive_check.setChecked(True)
        scan = QPushButton(T["scan"], self)
        scan.setProperty("fmRole", "primary")
        scan.clicked.connect(self.start_scan)
        self.cancel_button = QPushButton(T["cancel"], self)
        self.cancel_button.setProperty("fmRole", "danger")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_operation)
        options.addWidget(QLabel(T["minimum_size"], self))
        options.addWidget(self.minimum_size)
        options.addWidget(self.recursive_check)
        options.addStretch(1)
        options.addWidget(scan)
        options.addWidget(self.cancel_button)
        layout.addLayout(options)

        actions = QHBoxLayout()
        mark = QPushButton(T["mark_duplicates"], self)
        unmark = QPushButton(T["unmark_duplicates"], self)
        trash = QPushButton(T["trash_selected"], self)
        delete = QPushButton(T["delete_selected"], self)
        trash.setProperty("fmRole", "primary")
        delete.setProperty("fmRole", "danger")
        mark.clicked.connect(self.mark_duplicates)
        unmark.clicked.connect(self.unmark_all)
        trash.clicked.connect(self.delete_to_trash)
        delete.clicked.connect(self.delete_permanently)
        for button in (mark, unmark, trash, delete):
            actions.addWidget(button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.results_layout.setContentsMargins(5, 5, 5, 5)
        self.results_layout.setSpacing(8)
        self.results_layout.addStretch(1)
        self.scroll.setWidget(self.results_widget)
        layout.addWidget(self.scroll, 1)
        self.summary = QLabel(T["ready"], self)
        self.summary.setProperty("fmRole", "muted")
        layout.addWidget(self.summary)

    def choose_folder(self) -> None:
        """Choose the folder for the duplicate scan."""
        selected = QFileDialog.getExistingDirectory(self, T["select_folder"], self.folder_edit.text())
        if selected:
            self.folder_edit.setText(selected)
            self.config.set("last_paths.duplicates", selected)

    def start_scan(self) -> None:
        """Start staged duplicate detection in a worker thread."""
        root = Path(self.folder_edit.text().strip())
        if not root.is_dir():
            self.status_message.emit(T["select_folder"])
            return
        self.config.set("last_paths.duplicates", str(root))
        self._clear_results()
        self._thread = QThread(self)
        self._worker = DuplicateWorker(root, int(self.minimum_size.value() * 1024), self.recursive_check.isChecked())
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.phase.connect(self.status_message)
        self._worker.progress.connect(self.progress_changed)
        self._worker.groups_found.connect(self.show_groups)
        self._worker.error.connect(lambda message: self.status_message.emit(f"{T['status_error']}: {message}"))
        self._worker.finished.connect(self._scan_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()
        self.cancel_button.setVisible(True)
        self.busy_changed.emit(True)

    @Slot(object)
    def show_groups(self, groups: list[list[str]]) -> None:
        """Render duplicate groups as checkable cards."""
        self._groups = groups
        self._checks.clear()
        self._clear_results()
        recoverable = 0
        for number, group in enumerate(groups, 1):
            card = QFrame(self.results_widget)
            card.setProperty("fmRole", "group")
            card_layout = QVBoxLayout(card)
            size = 0
            paths = [Path(value) for value in group]
            try:
                size = paths[0].stat().st_size
            except (OSError, IndexError):
                pass
            recoverable += max(0, len(paths) - 1) * size
            heading = QLabel(T["duplicate_group"].format(number=number, count=len(paths), size=format_size(size)), card)
            heading.setProperty("fmRole", "section")
            card_layout.addWidget(heading)
            for index, path in enumerate(paths):
                original = index == 0
                try:
                    modified = format_datetime(path.stat().st_mtime)
                except OSError:
                    modified = "—"
                label = f"{T['keep_original'] if original else path.name}\n{path} | {modified}"
                checkbox = QCheckBox(label, card)
                checkbox.setChecked(not original)
                checkbox.setEnabled(not original)
                self._checks.append((checkbox, path, original))
                card_layout.addWidget(checkbox)
            self.results_layout.insertWidget(self.results_layout.count() - 1, card)
        self.summary.setText(T["duplicate_summary"].format(groups=len(groups), size=format_size(recoverable)))

    def _clear_results(self) -> None:
        """Remove old result cards from the scroll area."""
        while self.results_layout.count() > 1:
            item = self.results_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def _scan_finished(self) -> None:
        """Hide the scan controls after the worker stops."""
        self.cancel_button.setVisible(False)
        self.busy_changed.emit(False)

    def mark_duplicates(self) -> None:
        """Select every file except the first one in each group."""
        for checkbox, _path, original in self._checks:
            if not original:
                checkbox.setChecked(True)

    def unmark_all(self) -> None:
        """Clear all removable duplicate selections."""
        for checkbox, _path, original in self._checks:
            if not original:
                checkbox.setChecked(False)

    def _selected_paths(self) -> list[Path]:
        """Return checked duplicate paths."""
        return [path for checkbox, path, original in self._checks if checkbox.isChecked() and not original]

    def delete_to_trash(self) -> None:
        """Confirm and move selected duplicates to the system trash."""
        paths = self._selected_paths()
        if not paths:
            self.status_message.emit(T["nothing_to_do"])
            return
        answer = QMessageBox.question(self, T["trash_selected"], f"Удалить в корзину отмеченные файлы: {len(paths)}?")
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._delete_paths(paths, permanent=False)

    def delete_permanently(self) -> None:
        """Confirm twice before permanently deleting selected files."""
        paths = self._selected_paths()
        if not paths:
            self.status_message.emit(T["nothing_to_do"])
            return
        answer = QMessageBox.warning(
            self,
            T["delete_selected"],
            f"Удалить файлы без возможности восстановления: {len(paths)}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self._delete_paths(paths, permanent=True)

    def _delete_paths(self, paths: list[Path], permanent: bool) -> None:
        """Delete paths safely and report skipped entries."""
        deleted = 0
        for path in paths:
            try:
                path.unlink() if permanent else send_to_trash(path)
                deleted += 1
            except (PermissionError, FileNotFoundError, OSError, RuntimeError) as error:
                LOGGER.warning("Could not delete %s: %s", path, error)
        self.status_message.emit(f"Удалено файлов: {deleted} из {len(paths)}")
        self.unmark_all()

    def cancel_operation(self) -> None:
        """Request cancellation of the active duplicate scan."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.requestInterruption()
            self.status_message.emit(T["cancel"])
