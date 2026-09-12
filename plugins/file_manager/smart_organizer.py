"""Automatic file sorting page and background worker."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
    QRadioButton,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from plugins.file_manager.styles import DEFAULT_RULES, TEXTS as T
from plugins.file_manager.utils import FileManagerConfig, iter_files, unique_destination

LOGGER = logging.getLogger(__name__)


class OrganizeWorker(QObject):
    """Scan and optionally move or copy files according to extension rules."""

    progress = Signal(int, int)
    log = Signal(str)
    error = Signal(str)
    finished = Signal(int, int)

    def __init__(self, root: Path, rules: list[tuple[str, str, str]], recursive: bool, copy_mode: bool, preview: bool) -> None:
        """Store sorting options for the worker thread."""
        super().__init__()
        self.root = root
        self.rules = rules
        self.recursive = recursive
        self.copy_mode = copy_mode
        self.preview = preview

    @Slot()
    def run(self) -> None:
        """Collect files and execute or preview their destinations."""
        processed = 0
        try:
            files = list(iter_files(self.root, self.recursive))
            total = len(files)
            if total == 0:
                self.finished.emit(0, 0)
                return
            for source in files:
                if QThread.currentThread().isInterruptionRequested():
                    break
                destination_folder = self._destination_for(source)
                destination_folder.mkdir(parents=True, exist_ok=True) if not self.preview else None
                target = unique_destination(destination_folder / source.name)
                relative_target = target.relative_to(self.root) if target.is_relative_to(self.root) else target
                if not self.preview:
                    try:
                        if self.copy_mode:
                            shutil.copy2(source, target)
                        else:
                            shutil.move(str(source), str(target))
                        self.log.emit(f"[OK] {source.name} -> /{relative_target.parent}")
                    except (PermissionError, FileNotFoundError, OSError) as error:
                        self.log.emit(f"[ERROR] {source.name}: {error}")
                else:
                    self.log.emit(f"[PREVIEW] {source.name} -> /{relative_target.parent}")
                processed += 1
                self.progress.emit(processed, total)
            self.finished.emit(processed, total)
        except (PermissionError, FileNotFoundError, OSError, ValueError) as error:
            self.error.emit(str(error))
            self.finished.emit(processed, processed)

    def _destination_for(self, source: Path) -> Path:
        """Resolve a target folder from the first matching extension rule."""
        suffix = source.suffix.lower()
        for _category, extensions, destination in self.rules:
            if suffix in {item.lower() for item in extensions.split()}:
                return self.root / destination.strip("/\\")
        return self.root / "Other"


class SmartOrganizerPage(QWidget):
    """Page for previewing and executing extension-based file sorting."""

    status_message = Signal(str)
    progress_changed = Signal(int, int)
    busy_changed = Signal(bool)
    cancel_requested = Signal()

    def __init__(self, config: FileManagerConfig, parent: QWidget | None = None) -> None:
        """Create the organizer and restore saved rules and folder."""
        super().__init__(parent)
        self.config = config
        self._thread: QThread | None = None
        self._worker: OrganizeWorker | None = None
        self._build_ui()
        self._load_rules()

    def _build_ui(self) -> None:
        """Build folder, rules, options, action and log controls."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        title = QLabel(T["sort"], self)
        title.setProperty("fmRole", "section")
        layout.addWidget(title)

        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit(self.config.get("last_paths.sort", ""), self)
        self.folder_edit.setPlaceholderText(T["folder_placeholder"])
        folder_row.addWidget(self.folder_edit, 1)
        browse = QPushButton(T["browse"], self)
        browse.clicked.connect(self.choose_folder)
        folder_row.addWidget(browse)
        layout.addLayout(folder_row)

        self.rules = QTableWidget(0, 3, self)
        self.rules.setHorizontalHeaderLabels([T["category"], T["extensions"], T["destination"]])
        self.rules.horizontalHeader().setStretchLastSection(True)
        self.rules.setColumnWidth(0, 150)
        self.rules.setColumnWidth(1, 360)
        self.rules.setColumnWidth(2, 150)
        layout.addWidget(self.rules, 1)
        rule_buttons = QHBoxLayout()
        add = QPushButton(T["add_rule"], self)
        remove = QPushButton(T["remove_rule"], self)
        add.clicked.connect(self.add_rule)
        remove.clicked.connect(self.remove_rule)
        rule_buttons.addWidget(add)
        rule_buttons.addWidget(remove)
        rule_buttons.addStretch(1)
        layout.addLayout(rule_buttons)

        options = QHBoxLayout()
        self.move_radio = QRadioButton(T["move"], self)
        self.move_radio.setChecked(True)
        self.copy_radio = QRadioButton(T["copy"], self)
        self.recursive_check = QCheckBox(T["include_subfolders"], self)
        self.recursive_check.setChecked(True)
        options.addWidget(self.move_radio)
        options.addWidget(self.copy_radio)
        options.addSpacing(12)
        options.addWidget(self.recursive_check)
        options.addStretch(1)
        layout.addLayout(options)

        actions = QHBoxLayout()
        preview = QPushButton(T["preview"], self)
        execute = QPushButton(T["execute"], self)
        preview.clicked.connect(lambda: self.start_operation(True))
        execute.setProperty("fmRole", "primary")
        execute.clicked.connect(lambda: self.start_operation(False))
        self.cancel_button = QPushButton(T["cancel"], self)
        self.cancel_button.setProperty("fmRole", "danger")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_operation)
        actions.addWidget(preview)
        actions.addWidget(execute)
        actions.addWidget(self.cancel_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.log = QTextEdit(self)
        self.log.setReadOnly(True)
        self.log.setPlaceholderText(T["operation_log"])
        self.log.setMinimumHeight(110)
        layout.addWidget(self.log)

    def _load_rules(self) -> None:
        """Load saved rules or populate the default categories."""
        saved = self.config.get("sort_rules", [])
        rules = saved if isinstance(saved, list) and saved else [list(item) for item in DEFAULT_RULES]
        for rule in rules:
            if isinstance(rule, (list, tuple)) and len(rule) == 3:
                self._append_rule(str(rule[0]), str(rule[1]), str(rule[2]))

    def _append_rule(self, category: str, extensions: str, destination: str) -> None:
        """Append an editable rule row."""
        row = self.rules.rowCount()
        self.rules.insertRow(row)
        clean_destination = destination.strip("/\\")
        for column, value in enumerate((category, extensions, f"/{clean_destination}")):
            self.rules.setItem(row, column, QTableWidgetItem(value))

    def add_rule(self) -> None:
        """Add an empty sorting rule."""
        self._append_rule("Новая категория", ".ext", "/Other")

    def remove_rule(self) -> None:
        """Remove the selected sorting rule."""
        row = self.rules.currentRow()
        if row >= 0:
            self.rules.removeRow(row)
            self._save_rules()

    def _save_rules(self) -> list[tuple[str, str, str]]:
        """Read and persist table rules."""
        rules: list[tuple[str, str, str]] = []
        for row in range(self.rules.rowCount()):
            values = [self.rules.item(row, column).text().strip() if self.rules.item(row, column) else "" for column in range(3)]
            rules.append((values[0], values[1], values[2].strip("/\\")))
        self.config.set("sort_rules", [list(rule) for rule in rules])
        return rules

    def choose_folder(self) -> None:
        """Choose the source folder for sorting."""
        selected = QFileDialog.getExistingDirectory(self, T["select_folder"], self.folder_edit.text())
        if selected:
            self.folder_edit.setText(selected)
            self.config.set("last_paths.sort", selected)

    def start_operation(self, preview: bool) -> None:
        """Start preview or execution in a worker thread."""
        root = Path(self.folder_edit.text().strip())
        if not root.is_dir():
            self.status_message.emit(T["select_folder"])
            return
        rules = self._save_rules()
        self.log.clear()
        self.config.set("last_paths.sort", str(root))
        self._thread = QThread(self)
        self._worker = OrganizeWorker(root, rules, self.recursive_check.isChecked(), self.copy_radio.isChecked(), preview)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log.connect(self.log.append)
        self._worker.progress.connect(self.progress_changed)
        self._worker.error.connect(lambda message: self.status_message.emit(f"{T['status_error']}: {message}"))
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()
        self.cancel_button.setVisible(True)
        self.busy_changed.emit(True)
        self.status_message.emit(T["preview"] if preview else T["execute"])

    def _on_finished(self, processed: int, total: int) -> None:
        """Update status after sorting completes or is cancelled."""
        self.cancel_button.setVisible(False)
        self.busy_changed.emit(False)
        self.status_message.emit(f"Обработано {processed} из {total} файлов")

    def cancel_operation(self) -> None:
        """Request cancellation of the active sorting worker."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.requestInterruption()
            self.status_message.emit(T["cancel"])
