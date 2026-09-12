"""Bulk rename page with live preview and undo history."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugins.file_manager.styles import TEXTS as T
from plugins.file_manager.utils import FileManagerConfig, format_size, iter_files, remove_characters

LOGGER = logging.getLogger(__name__)


class RenameScanWorker(QObject):
    """Collect files for a rename preview in a worker thread."""

    result = Signal(object)
    error = Signal(str)

    def __init__(self, folder: Path) -> None:
        """Store the folder to scan."""
        super().__init__()
        self.folder = folder

    @Slot()
    def run(self) -> None:
        """Emit regular files from the selected folder."""
        try:
            self.result.emit(list(iter_files(self.folder, False)))
        except (PermissionError, FileNotFoundError, OSError) as error:
            self.error.emit(str(error))


class RenameWorker(QObject):
    """Execute a validated old-to-new path mapping."""

    progress = Signal(int, int)
    log = Signal(str)
    error = Signal(str)
    completed = Signal(object)
    finished = Signal()

    def __init__(self, mapping: list[tuple[Path, Path]]) -> None:
        """Store the mapping to apply."""
        super().__init__()
        self.mapping = mapping

    @Slot()
    def run(self) -> None:
        """Rename files one by one, retaining successful changes for undo."""
        changed: list[tuple[Path, Path]] = []
        total = len(self.mapping)
        try:
            for index, (old, new) in enumerate(self.mapping, 1):
                if QThread.currentThread().isInterruptionRequested():
                    break
                try:
                    if old == new:
                        self.progress.emit(index, max(1, total))
                        continue
                    if new.exists():
                        self.log.emit(f"[ERROR] {new.name}: имя уже занято")
                        continue
                    old.rename(new)
                    changed.append((old, new))
                    self.log.emit(f"[OK] {old.name} -> {new.name}")
                except (PermissionError, FileNotFoundError, OSError) as error:
                    self.log.emit(f"[ERROR] {old.name}: {error}")
                self.progress.emit(index, max(1, total))
            self.completed.emit(changed)
        except (PermissionError, FileNotFoundError, OSError) as error:
            self.error.emit(str(error))
        finally:
            self.finished.emit()


class BulkRenamePage(QWidget):
    """Page for pattern-based batch file renaming."""

    status_message = Signal(str)
    progress_changed = Signal(int, int)
    busy_changed = Signal(bool)
    cancel_requested = Signal()

    def __init__(self, config: FileManagerConfig, parent: QWidget | None = None) -> None:
        """Create rename controls and an empty preview."""
        super().__init__(parent)
        self.config = config
        self._thread: QThread | None = None
        self._worker: QObject | None = None
        self._files: list[Path] = []
        self._history: list[list[tuple[Path, Path]]] = []
        self._mapping: list[tuple[Path, Path]] = []
        self._build_ui()

    def _build_ui(self) -> None:
        """Build folder, template controls and preview table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        title = QLabel(T["rename"], self)
        title.setProperty("fmRole", "section")
        layout.addWidget(title)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(self.config.get("last_paths.rename", ""), self)
        self.folder_edit.setPlaceholderText(T["folder_placeholder"])
        folder_row.addWidget(self.folder_edit, 1)
        browse = QPushButton(T["browse"], self)
        refresh = QPushButton(T["refresh"], self)
        browse.clicked.connect(self.choose_folder)
        refresh.clicked.connect(self.load_files)
        folder_row.addWidget(browse)
        folder_row.addWidget(refresh)
        layout.addLayout(folder_row)

        settings = QFrame(self)
        settings.setProperty("fmRole", "group")
        settings_layout = QVBoxLayout(settings)
        settings_layout.setContentsMargins(10, 8, 10, 8)
        pattern_row = QHBoxLayout()
        pattern_row.addWidget(QLabel(T["pattern"], settings))
        self.pattern_edit = QLineEdit("{name}_{num:03d}", settings)
        self.pattern_edit.setPlaceholderText(T["pattern_hint"])
        pattern_row.addWidget(self.pattern_edit, 1)
        pattern_row.addWidget(QLabel(T["start_number"], settings))
        self.start_number = QSpinBox(settings)
        self.start_number.setRange(0, 999999)
        self.start_number.setValue(1)
        pattern_row.addWidget(self.start_number)
        pattern_row.addWidget(QLabel(T["step"], settings))
        self.step = QSpinBox(settings)
        self.step.setRange(1, 999999)
        self.step.setValue(1)
        pattern_row.addWidget(self.step)
        settings_layout.addLayout(pattern_row)

        replace_row = QHBoxLayout()
        self.find_edit = QLineEdit(settings)
        self.find_edit.setPlaceholderText(T["find"])
        self.replace_edit = QLineEdit(settings)
        self.replace_edit.setPlaceholderText(T["replace"])
        self.case_combo = QComboBox(settings)
        self.case_combo.addItem(T["case_keep"], "keep")
        self.case_combo.addItem(T["case_upper"], "upper")
        self.case_combo.addItem(T["case_lower"], "lower")
        self.case_combo.addItem(T["case_title"], "title")
        self.remove_edit = QLineEdit(settings)
        self.remove_edit.setPlaceholderText(T["remove_chars"])
        replace_row.addWidget(self.find_edit)
        replace_row.addWidget(self.replace_edit)
        replace_row.addWidget(QLabel(T["case"], settings))
        replace_row.addWidget(self.case_combo)
        replace_row.addWidget(self.remove_edit, 1)
        settings_layout.addLayout(replace_row)
        layout.addWidget(settings)

        for control in (self.pattern_edit, self.start_number, self.step, self.find_edit, self.replace_edit, self.remove_edit):
            signal = getattr(control, "textChanged", None) or getattr(control, "valueChanged", None)
            if signal is not None:
                signal.connect(self.update_preview)
        self.case_combo.currentIndexChanged.connect(self.update_preview)

        actions = QHBoxLayout()
        self.rename_button = QPushButton(T["rename_button"], self)
        self.rename_button.setProperty("fmRole", "primary")
        self.rename_button.clicked.connect(self.start_rename)
        self.undo_button = QPushButton(T["undo_rename"], self)
        self.undo_button.clicked.connect(self.undo_last)
        self.undo_button.setEnabled(False)
        self.cancel_button = QPushButton(T["cancel"], self)
        self.cancel_button.setProperty("fmRole", "danger")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_operation)
        actions.addWidget(self.rename_button)
        actions.addWidget(self.undo_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.table = QTableWidget(0, 2, self)
        self.table.setHorizontalHeaderLabels([T["file_name"], "Новое имя"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 300)
        layout.addWidget(self.table, 1)
        self.log = QLabel(T["ready"], self)
        self.log.setProperty("fmRole", "muted")
        layout.addWidget(self.log)

    def choose_folder(self) -> None:
        """Choose a folder and load its files."""
        selected = QFileDialog.getExistingDirectory(self, T["select_folder"], self.folder_edit.text())
        if selected:
            self.folder_edit.setText(selected)
            self.config.set("last_paths.rename", selected)
            self.load_files()

    def load_files(self) -> None:
        """Load regular files from the selected folder in a worker thread."""
        folder = Path(self.folder_edit.text().strip())
        if not folder.is_dir():
            self.status_message.emit(T["select_folder"])
            return
        self.config.set("last_paths.rename", str(folder))
        thread = QThread(self)
        worker = RenameScanWorker(folder)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.result.connect(self.set_files)
        worker.error.connect(lambda message: self.status_message.emit(f"{T['status_error']}: {message}"))
        worker.error.connect(thread.quit)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(worker.deleteLater)
        worker.result.connect(thread.quit)
        self._thread = thread
        self._worker = worker
        thread.start()
        self.busy_changed.emit(True)

    @Slot(object)
    def set_files(self, files: list[Path]) -> None:
        """Set files and refresh the preview table."""
        self._files = sorted(files, key=lambda path: path.name.casefold())
        self.update_preview()
        self.busy_changed.emit(False)
        self.status_message.emit(f"Загружено файлов: {len(self._files)}")

    def _render_name(self, path: Path, number: int) -> str:
        """Render one new filename from the configured variables."""
        try:
            stat = path.stat()
            values = {
                "name": path.stem,
                "ext": path.suffix.lstrip("."),
                "num": number,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d"),
                "size": format_size(stat.st_size),
            }
            rendered = self.pattern_edit.text().format_map(values)
        except (KeyError, ValueError, IndexError, OSError):
            rendered = path.stem
        rendered = rendered or path.stem
        find_value = self.find_edit.text()
        if find_value:
            rendered = rendered.replace(find_value, self.replace_edit.text())
        case = self.case_combo.currentData()
        if case == "upper":
            rendered = rendered.upper()
        elif case == "lower":
            rendered = rendered.lower()
        elif case == "title":
            rendered = rendered.title()
        rendered = remove_characters(rendered, self.remove_edit.text())
        if not Path(rendered).suffix:
            rendered += path.suffix
        return rendered

    def update_preview(self) -> None:
        """Recalculate the table preview after any template change."""
        if not hasattr(self, "table"):
            return
        self._mapping = []
        self.table.setRowCount(0)
        occupied: set[str] = set()
        conflicts = False
        for index, path in enumerate(self._files):
            new_name = self._render_name(path, self.start_number.value() + index * self.step.value())
            target = path.with_name(new_name)
            if target.exists() and target != path or str(target).casefold() in occupied:
                conflicts = True
            occupied.add(str(target).casefold())
            self._mapping.append((path, target))
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(path.name))
            self.table.setItem(row, 1, QTableWidgetItem(new_name))
        if conflicts:
            self.log.setText(T["conflict"])
        elif self._files:
            self.log.setText(f"Предпросмотр готов: {len(self._files)} файлов")
        else:
            self.log.setText(T["no_files"])

    def start_rename(self) -> None:
        """Validate conflicts and run the rename operation in a worker."""
        if not self._mapping:
            self.status_message.emit(T["nothing_to_do"])
            return
        conflicts = [new for old, new in self._mapping if new.exists() and new != old]
        if conflicts:
            QMessageBox.warning(self, T["rename_button"], T["conflict"])
            return
        self._run_mapping(self._mapping)

    def _run_mapping(self, mapping: list[tuple[Path, Path]]) -> None:
        """Start a rename worker for a mapping."""
        self._thread = QThread(self)
        self._worker = RenameWorker(mapping)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress_changed)
        self._worker.log.connect(self.log.setText)
        self._worker.error.connect(lambda message: self.status_message.emit(f"{T['status_error']}: {message}"))
        self._worker.completed.connect(self._rename_completed)
        self._worker.finished.connect(self._rename_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()
        self.cancel_button.setVisible(True)
        self.busy_changed.emit(True)

    @Slot(object)
    def _rename_completed(self, changed: list[tuple[Path, Path]]) -> None:
        """Store a successful operation for undo."""
        if changed:
            self._history.append(changed)
            self._history = self._history[-10:]
            self.undo_button.setEnabled(True)
        self.status_message.emit(f"Переименовано файлов: {len(changed)}")

    def _rename_finished(self) -> None:
        """Reset controls when the rename worker stops."""
        self.cancel_button.setVisible(False)
        self.busy_changed.emit(False)
        self.update_preview()

    def undo_last(self) -> None:
        """Restore the previous successful mapping."""
        if not self._history:
            return
        mapping = [(new, old) for old, new in reversed(self._history.pop())]
        self._run_mapping(mapping)
        self.undo_button.setEnabled(bool(self._history))

    def cancel_operation(self) -> None:
        """Request cancellation of the active rename worker."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.requestInterruption()
            self.status_message.emit(T["cancel"])
