"""Shared filesystem, formatting and worker helpers for the file manager."""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
import platform
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

try:
    import humanize
except ImportError:  # pragma: no cover - dependency is installed in normal use
    humanize = None  # type: ignore[assignment]

try:
    import send2trash
except ImportError:  # pragma: no cover - dependency is installed in normal use
    send2trash = None  # type: ignore[assignment]

try:
    import xxhash
except ImportError:  # pragma: no cover - dependency is installed in normal use
    xxhash = None  # type: ignore[assignment]

from PySide6.QtCore import QObject, Signal

from core.utils import load_icon
from plugins.file_manager.styles import TEXTS as T

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FileInfo:
    """Small immutable record used by search and rename previews."""

    path: Path
    size: int
    modified: float


class FileManagerConfig:
    """Thread-safe JSON configuration stored in the application's data folder."""

    DEFAULTS: dict[str, Any] = {
        "last_paths": {"sort": "", "duplicates": "", "rename": "", "space": "", "search": ""},
        "sort_rules": [],
        "search": {"max_results": 10000},
    }

    def __init__(self, path: Path | str | None = None) -> None:
        """Load configuration from disk or create it from defaults."""
        self.path = Path(path) if path else Path(__file__).resolve().parents[2] / "data" / "file_manager_config.json"
        self._lock = threading.RLock()
        self._data: dict[str, Any] = copy.deepcopy(self.DEFAULTS)
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """Return a value using dotted key notation."""
        with self._lock:
            current: Any = self._data
            for part in key.split("."):
                if not isinstance(current, dict) or part not in current:
                    return default
                current = current[part]
            return copy.deepcopy(current)

    def set(self, key: str, value: Any) -> None:
        """Set a value and save it immediately."""
        with self._lock:
            parts = key.split(".")
            current = self._data
            for part in parts[:-1]:
                if not isinstance(current.get(part), dict):
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = copy.deepcopy(value)
            self._save()

    def reset(self) -> None:
        """Restore module defaults."""
        with self._lock:
            self._data = copy.deepcopy(self.DEFAULTS)
            self._save()

    def _load(self) -> None:
        """Load and merge the JSON configuration without raising."""
        try:
            if self.path.exists():
                loaded = json.loads(self.path.read_text(encoding="utf-8"))
                self._merge(self._data, loaded)
            else:
                self._save()
        except (OSError, TypeError, json.JSONDecodeError) as error:
            LOGGER.warning("Could not load file manager configuration: %s", error)

    def _save(self) -> None:
        """Write the configuration through a temporary file."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(".tmp")
            temporary.write_text(json.dumps(self._data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            os.replace(temporary, self.path)
        except (OSError, TypeError, ValueError) as error:
            LOGGER.warning("Could not save file manager configuration: %s", error)

    @staticmethod
    def _merge(target: dict[str, Any], source: Any) -> None:
        """Merge known configuration keys recursively."""
        if not isinstance(source, dict):
            return
        for key, value in source.items():
            if key not in target:
                continue
            if isinstance(target[key], dict) and isinstance(value, dict):
                FileManagerConfig._merge(target[key], value)
            else:
                target[key] = value


class WorkerSignals(QObject):
    """Common signals for background filesystem workers."""

    progress = Signal(int, int)
    status = Signal(str)
    error = Signal(str)
    finished = Signal()


def format_size(value: int | float) -> str:
    """Return a readable binary file size."""
    try:
        number = max(0, int(value))
    except (TypeError, ValueError):
        return "0 B"
    if humanize is not None:
        try:
            return humanize.naturalsize(number, binary=True, format="%.1f")
        except (AttributeError, TypeError, ValueError):
            pass
    units = ("B", "KB", "MB", "GB", "TB")
    position = 0
    amount = float(number)
    while amount >= 1024 and position < len(units) - 1:
        amount /= 1024
        position += 1
    return f"{amount:.1f} {units[position]}" if position else f"{number} B"


def icon_for_path(path: Path):
    """Return a safe icon for a file or directory."""
    return load_icon("folder.svg" if path.is_dir() else "file.svg")


def iter_files(root: Path, recursive: bool = True) -> Iterator[Path]:
    """Yield regular files below a folder while skipping inaccessible entries."""
    try:
        with os.scandir(root) as entries:
            for entry in entries:
                try:
                    if entry.is_file(follow_symlinks=False):
                        yield Path(entry.path)
                    elif recursive and entry.is_dir(follow_symlinks=False):
                        yield from iter_files(Path(entry.path), True)
                except (PermissionError, FileNotFoundError, OSError) as error:
                    LOGGER.debug("Skipped %s: %s", entry.path, error)
    except (PermissionError, FileNotFoundError, NotADirectoryError, OSError) as error:
        LOGGER.debug("Could not scan %s: %s", root, error)


def safe_file_info(path: Path) -> FileInfo | None:
    """Read file metadata without allowing a disappearing file to fail a scan."""
    try:
        stat = path.stat()
        return FileInfo(path, stat.st_size, stat.st_mtime)
    except (PermissionError, FileNotFoundError, OSError):
        return None


def format_datetime(timestamp: float) -> str:
    """Format a modification timestamp for the Russian interface."""
    try:
        return datetime.fromtimestamp(timestamp).strftime("%d.%m.%Y %H:%M")
    except (OSError, OverflowError, ValueError):
        return "—"


def parse_extensions(value: str) -> set[str]:
    """Normalize a space or comma separated extension list."""
    result: set[str] = set()
    for token in re.split(r"[\s,;]+", value.lower().strip()):
        if not token:
            continue
        result.add(token if token.startswith(".") else f".{token}")
    return result


def unique_destination(path: Path) -> Path:
    """Return a non-existing path by appending a numeric suffix."""
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    number = 1
    while True:
        candidate = path.with_name(f"{stem}_{number}{suffix}")
        if not candidate.exists():
            return candidate
        number += 1


def hash_file(path: Path, partial: bool = False, chunk_size: int = 1024 * 1024) -> str | None:
    """Hash a file with xxhash, falling back to hashlib when unavailable."""
    try:
        hasher = xxhash.xxh64() if xxhash is not None else hashlib.blake2b(digest_size=16)
        remaining = 4096 if partial else None
        with path.open("rb") as source:
            while True:
                size = chunk_size if remaining is None else min(chunk_size, remaining)
                block = source.read(size)
                if not block:
                    break
                hasher.update(block)
                if remaining is not None:
                    remaining -= len(block)
                    if remaining <= 0:
                        break
        return hasher.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None


def send_to_trash(path: Path) -> None:
    """Move a path to the operating system trash."""
    if send2trash is None:
        raise RuntimeError(T["library_missing"])
    send2trash.send2trash(str(path))


def open_with_system(path: Path) -> None:
    """Open a file or directory in the default system application."""
    if platform.system() == "Windows":
        os.startfile(str(path))  # type: ignore[attr-defined]
    elif platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)], close_fds=True)
    else:
        subprocess.Popen(["xdg-open", str(path)], close_fds=True)


def remove_characters(value: str, characters: str) -> str:
    """Remove every character listed in ``characters`` from a string."""
    return "".join(character for character in value if character not in characters)


def is_probably_text(path: Path) -> bool:
    """Return whether an extension is commonly associated with text."""
    return path.suffix.lower() in {
        ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".xml",
        ".yaml", ".yml", ".ini", ".cfg", ".toml", ".csv", ".log", ".sql",
    }
