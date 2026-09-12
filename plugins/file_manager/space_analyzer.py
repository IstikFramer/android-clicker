"""Disk usage analyzer with treemap, type chart and top-file table."""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

try:
    import psutil
except ImportError:  # pragma: no cover - dependency is installed in normal use
    psutil = None  # type: ignore[assignment]

from PySide6.QtCore import QObject, QRectF, QThread, Qt, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from plugins.file_manager.styles import TEXTS as T
from plugins.file_manager.utils import FileManagerConfig, format_size

LOGGER = logging.getLogger(__name__)

TYPE_COLORS: dict[str, str] = {
    ".jpg": "#00adb5", ".jpeg": "#00adb5", ".png": "#00cfd8", ".gif": "#2ecc71",
    ".mp4": "#f39c12", ".mkv": "#f39c12", ".mp3": "#9b59b6", ".wav": "#9b59b6",
    ".pdf": "#e74c3c", ".docx": "#3498db", ".xlsx": "#2ecc71", ".py": "#f1c40f",
}


class SpaceWorker(QObject):
    """Recursively collect sizes and top files for one directory."""

    progress = Signal(int, int)
    result = Signal(object)
    error = Signal(str)
    finished = Signal()

    def __init__(self, root: Path) -> None:
        """Store the directory to analyze."""
        super().__init__()
        self.root = root
        self._visited = 0
        self._files: list[dict[str, Any]] = []
        self._types: dict[str, int] = defaultdict(int)

    @Slot()
    def run(self) -> None:
        """Scan the directory and emit a serializable analysis result."""
        try:
            children: list[dict[str, Any]] = []
            total = self._scan_directory(self.root, children)
            disk_total, disk_used, disk_free = total, total, 0
            if psutil is not None:
                try:
                    usage = psutil.disk_usage(self.root.anchor or str(self.root))
                    disk_total, disk_used, disk_free = usage.total, usage.used, usage.free
                except (OSError, ValueError):
                    pass
            self._files.sort(key=lambda item: item["size"], reverse=True)
            self.result.emit(
                {
                    "root": str(self.root),
                    "total": total,
                    "disk_total": disk_total,
                    "disk_used": disk_used,
                    "disk_free": disk_free,
                    "children": children,
                    "top_files": self._files[:50],
                    "types": dict(self._types),
                }
            )
        except (PermissionError, FileNotFoundError, OSError, ValueError) as error:
            self.error.emit(str(error))
        finally:
            self.finished.emit()

    def _scan_directory(self, path: Path, children: list[dict[str, Any]] | None = None) -> int:
        """Return a directory size and optionally record its direct children."""
        total = 0
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if QThread.currentThread().isInterruptionRequested():
                        return total
                    child = Path(entry.path)
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            size = self._scan_directory(child)
                            is_directory = True
                        elif entry.is_file(follow_symlinks=False):
                            size = entry.stat(follow_symlinks=False).st_size
                            is_directory = False
                            suffix = child.suffix.lower() or "Без расширения"
                            self._types[suffix] += size
                            self._files.append(
                                {"name": child.name, "path": str(child), "size": size, "modified": child.stat().st_mtime, "type": suffix}
                            )
                        else:
                            continue
                        total += size
                        if children is not None:
                            children.append({"name": child.name, "path": str(child), "size": size, "is_dir": is_directory})
                        self._visited += 1
                        if self._visited % 25 == 0:
                            self.progress.emit(self._visited, self._visited + 100)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
        except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
            return total
        return total


class TreemapItem(QGraphicsRectItem):
    """Interactive treemap rectangle for a file or directory."""

    def __init__(self, rect: Any, data: dict[str, Any], on_open: Callable[[Path], None]) -> None:
        """Create a hoverable rectangle with drill-down callback."""
        super().__init__(rect)
        self.data = data
        self.on_open = on_open
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{data['name']}\n{format_size(data['size'])}\n{data['path']}")
        color = QColor(TYPE_COLORS.get(Path(str(data["name"])).suffix.lower(), "#0f3460"))
        color.setAlpha(210 if data.get("is_dir") else 180)
        self.setBrush(color)
        self.setPen(QPen(QColor("#1a1a2e"), 1))

    def mousePressEvent(self, event: Any) -> None:
        """Open directories on click."""
        if self.data.get("is_dir"):
            self.on_open(Path(self.data["path"]))
        super().mousePressEvent(event)

    def hoverEnterEvent(self, event: Any) -> None:
        """Brighten the rectangle while hovered."""
        color = self.brush().color()
        color.setAlpha(255)
        self.setBrush(color)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: Any) -> None:
        """Restore the normal rectangle opacity."""
        color = self.brush().color()
        color.setAlpha(210 if self.data.get("is_dir") else 180)
        self.setBrush(color)
        super().hoverLeaveEvent(event)


class PieChart(QWidget):
    """Minimal QPainter pie chart for file type distribution."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create an empty chart."""
        super().__init__(parent)
        self.values: dict[str, int] = {}
        self.setMinimumHeight(190)

    def set_values(self, values: dict[str, int]) -> None:
        """Set type sizes and repaint the chart."""
        self.values = values
        self.update()

    def paintEvent(self, event: Any) -> None:
        """Draw proportional file-type sectors."""
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        total = sum(self.values.values())
        if total <= 0:
            painter.setPen(QColor("#8a8a8a"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, T["no_files"])
            return
        size = min(self.width(), self.height()) - 20
        rect = self.rect().center()
        pie_rect = QRectF(rect.x() - size / 2, rect.y() - size / 2, size, size)
        start = 0
        for extension, amount in sorted(self.values.items(), key=lambda item: item[1], reverse=True):
            span = int(360 * 16 * amount / total)
            painter.setBrush(QColor(TYPE_COLORS.get(extension, "#0f3460")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPie(pie_rect, start, span)
            start += span


class SpaceAnalyzerPage(QWidget):
    """Analyze disk usage with a cached, drill-down treemap."""

    status_message = Signal(str)
    progress_changed = Signal(int, int)
    busy_changed = Signal(bool)
    cancel_requested = Signal()

    def __init__(self, config: FileManagerConfig, parent: QWidget | None = None) -> None:
        """Create analyzer controls and an empty visualization."""
        super().__init__(parent)
        self.config = config
        self._thread: QThread | None = None
        self._worker: SpaceWorker | None = None
        self._cache: dict[str, dict[str, Any]] = {}
        self._current_path = Path(config.get("last_paths.space", "") or Path.home())
        self._build_ui()

    def _build_ui(self) -> None:
        """Build folder picker, treemap, pie chart and top-file table."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)
        title = QLabel(T["space"], self)
        title.setProperty("fmRole", "section")
        layout.addWidget(title)
        row = QHBoxLayout()
        self.folder_edit = QLineEdit(str(self._current_path), self)
        self.folder_edit.setPlaceholderText(T["disk_folder"])
        row.addWidget(self.folder_edit, 1)
        browse = QPushButton(T["browse"], self)
        refresh = QPushButton(T["refresh"], self)
        up = QPushButton("Вверх", self)
        browse.clicked.connect(self.choose_folder)
        refresh.clicked.connect(self.refresh)
        up.clicked.connect(self.go_up)
        row.addWidget(browse)
        row.addWidget(up)
        row.addWidget(refresh)
        layout.addLayout(row)
        self.summary = QLabel(T["ready"], self)
        self.summary.setProperty("fmRole", "muted")
        layout.addWidget(self.summary)

        self.scene = QGraphicsScene(self)
        self.graphics = QGraphicsView(self.scene, self)
        self.graphics.setMinimumHeight(220)
        layout.addWidget(self.graphics, 1)

        lower = QHBoxLayout()
        self.table = QTableWidget(0, 4, self)
        self.table.setHorizontalHeaderLabels([T["file_name"], T["file_path"], T["file_size"], T["file_type"]])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 180)
        self.table.setColumnWidth(1, 310)
        self.table.setColumnWidth(2, 100)
        self.pie = PieChart(self)
        lower.addWidget(self.table, 3)
        lower.addWidget(self.pie, 2)
        layout.addLayout(lower, 1)
        self.refresh()

    def choose_folder(self) -> None:
        """Choose a folder for analysis."""
        selected = QFileDialog.getExistingDirectory(self, T["select_folder"], str(self._current_path))
        if selected:
            self._current_path = Path(selected)
            self.folder_edit.setText(selected)
            self.config.set("last_paths.space", selected)
            self.refresh()

    def refresh(self) -> None:
        """Invalidate the current cache and scan the selected path."""
        self._current_path = Path(self.folder_edit.text().strip())
        self._cache.pop(str(self._current_path), None)
        self.scan_current()

    def go_up(self) -> None:
        """Drill up one directory and use the cache when available."""
        parent = self._current_path.parent
        if parent != self._current_path:
            self._current_path = parent
            self.folder_edit.setText(str(parent))
            self.scan_current()

    def scan_current(self) -> None:
        """Render cached data or start a background scan."""
        if not self._current_path.is_dir():
            self.status_message.emit(T["select_folder"])
            return
        cached = self._cache.get(str(self._current_path))
        if cached is not None:
            self.show_result(cached)
            return
        self.config.set("last_paths.space", str(self._current_path))
        self._thread = QThread(self)
        self._worker = SpaceWorker(self._current_path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress_changed)
        self._worker.result.connect(self.show_result)
        self._worker.error.connect(lambda message: self.status_message.emit(f"{T['status_error']}: {message}"))
        self._worker.finished.connect(self._scan_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.start()
        self.busy_changed.emit(True)
        self.status_message.emit(T["scan"])

    @Slot(object)
    def show_result(self, result: dict[str, Any]) -> None:
        """Render one analyzer result and cache it for drill-down."""
        self._cache[result["root"]] = result
        total = result["disk_total"]
        used = result["disk_used"]
        free = result["disk_free"]
        self.summary.setText(T["summary"].format(total=format_size(total), used=format_size(used), free=format_size(free)))
        self.scene.clear()
        children = sorted(result["children"], key=lambda item: item["size"], reverse=True)
        scene_width = max(600, self.graphics.viewport().width() - 12)
        x, y, row_height = 0.0, 0.0, 92.0
        root_total = max(1, int(result["total"]))
        for child in children[:80]:
            width = max(36.0, scene_width * child["size"] / root_total)
            if x + width > scene_width:
                x = 0.0
                y += row_height
            item = TreemapItem((x, y, width - 3, row_height - 3), child, self.open_directory)
            self.scene.addItem(item)
            x += width
        self.scene.setSceneRect(0, 0, scene_width, max(200, y + row_height))
        self.table.setRowCount(0)
        for item in result["top_files"]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(item["path"]))
            self.table.setItem(row, 2, QTableWidgetItem(format_size(item["size"])))
            self.table.setItem(row, 3, QTableWidgetItem(item["type"]))
        self.pie.set_values(result["types"])
        self.status_message.emit(f"Проанализировано: {self._current_path}")

    def open_directory(self, path: Path) -> None:
        """Open a treemap directory and render its cached or new data."""
        self._current_path = path
        self.folder_edit.setText(str(path))
        self.scan_current()

    def _scan_finished(self) -> None:
        """Hide the shared progress state after analysis."""
        self.busy_changed.emit(False)

    def cancel_operation(self) -> None:
        """Request cancellation of the current analysis."""
        if self._thread is not None and self._thread.isRunning():
            self._thread.requestInterruption()
            self.status_message.emit(T["cancel"])
