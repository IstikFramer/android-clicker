"""LIFE OS — инструменты анализа системы: автозагрузка, процессы, диск, сеть.

В отличие от очистки эти средства почти ничего не удаляют: они показывают,
что происходит с компьютером. Единственное изменяющее действие —
отключение программы из автозагрузки, и оно требует подтверждения.

Приоритет — Windows; на других системах используются доступные аналоги.
"""
from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from .tools_engine import human_size

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# Ключи реестра, откуда Windows запускает программы при входе.
RUN_KEYS = (
    ("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Run"),
    ("HKLM", r"Software\Microsoft\Windows\CurrentVersion\Run"),
)


def _no_window() -> dict:
    """Аргументы subprocess, чтобы не мигала консоль на Windows."""
    if not IS_WIN:
        return {}
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {"startupinfo": si,
            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)}


# =========================================================== автозагрузка
@dataclass
class StartupItem:
    name: str
    command: str
    location: str            # HKCU / HKLM / Папка автозагрузки
    enabled: bool = True
    publisher: str = ""

    @property
    def exe_path(self) -> str:
        cmd = self.command.strip()
        if cmd.startswith('"'):
            return cmd.split('"')[1] if '"' in cmd[1:] else cmd
        return cmd.split(" ")[0]


def list_startup() -> list[StartupItem]:
    """Программы, стартующие вместе с системой."""
    out: list[StartupItem] = []
    if IS_WIN:
        import winreg
        roots = {"HKCU": winreg.HKEY_CURRENT_USER,
                 "HKLM": winreg.HKEY_LOCAL_MACHINE}
        for label, path in RUN_KEYS:
            try:
                key = winreg.OpenKey(roots[label], path)
            except OSError:
                continue
            with key:
                index = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, index)
                    except OSError:
                        break
                    index += 1
                    out.append(StartupItem(
                        name=name, command=str(value), location=label))
        # Папка «Автозагрузка»
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            folder = (Path(appdata) / "Microsoft" / "Windows" /
                      "Start Menu" / "Programs" / "Startup")
            if folder.exists():
                for f in folder.iterdir():
                    if f.name.lower().endswith((".lnk", ".exe", ".bat", ".cmd")):
                        out.append(StartupItem(
                            name=f.stem, command=str(f),
                            location="Папка автозагрузки"))
    else:
        autodir = Path.home() / ".config" / "autostart"
        if autodir.exists():
            for f in sorted(autodir.glob("*.desktop")):
                name, cmd = f.stem, ""
                try:
                    for line in f.read_text(errors="ignore").splitlines():
                        if line.startswith("Name="):
                            name = line[5:].strip()
                        elif line.startswith("Exec="):
                            cmd = line[5:].strip()
                except OSError:
                    pass
                out.append(StartupItem(name=name, command=cmd,
                                       location="Автозапуск сеанса"))
    out.sort(key=lambda i: i.name.lower())
    return out


def disable_startup(item: StartupItem) -> tuple[bool, str]:
    """Убирает программу из автозагрузки. Возвращает (успех, сообщение)."""
    if IS_WIN and item.location in ("HKCU", "HKLM"):
        import winreg
        root = (winreg.HKEY_CURRENT_USER if item.location == "HKCU"
                else winreg.HKEY_LOCAL_MACHINE)
        path = next(p for lbl, p in RUN_KEYS if lbl == item.location)
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, item.name)
            return True, "Удалено из автозагрузки."
        except PermissionError:
            return False, ("Недостаточно прав. Для записей HKLM нужен "
                           "запуск от администратора.")
        except OSError as exc:
            return False, f"Не удалось изменить запись: {exc}"
    # Файл в папке автозагрузки или .desktop — переносим в резерв
    src = Path(item.command if item.location != "HKCU" else item.exe_path)
    if src.exists():
        backup = Path.home() / ".lifeos" / "startup-disabled"
        backup.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(src), str(backup / src.name))
            return True, f"Перемещено в {backup}"
        except OSError as exc:
            return False, f"Не удалось переместить файл: {exc}"
    return False, "Запись не найдена."


# ==================================================== своя автозагрузка
def _own_launch_command() -> str:
    """Команда запуска этой копии программы.

    Для собранной версии это путь к самому EXE, для запуска из исходников —
    интерпретатор с main.py.
    """
    exe = Path(sys.executable).resolve()
    if getattr(sys, "frozen", False):
        return f'"{exe}"'
    main = Path(__file__).resolve().parents[1] / "main.py"
    return f'"{exe}" "{main}"'


def set_own_autostart(enabled: bool) -> tuple[bool, str]:
    """Включает или выключает запуск программы вместе с системой."""
    name = "LIFE OS"
    if IS_WIN:
        import winreg
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                winreg.KEY_SET_VALUE) as key:
                if enabled:
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ,
                                      _own_launch_command())
                else:
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
            return True, ""
        except OSError as exc:
            return False, str(exc)

    # Linux: файл .desktop в автозапуске рабочего стола
    autodir = Path.home() / ".config" / "autostart"
    target = autodir / "lifeos.desktop"
    try:
        if enabled:
            autodir.mkdir(parents=True, exist_ok=True)
            target.write_text(
                "[Desktop Entry]\nType=Application\nName=LIFE OS\n"
                f"Exec={_own_launch_command()}\nX-GNOME-Autostart-enabled=true\n",
                encoding="utf-8")
        elif target.exists():
            target.unlink()
        return True, ""
    except OSError as exc:
        return False, str(exc)


def own_autostart_enabled() -> bool:
    """Прописана ли программа в автозагрузке на самом деле."""
    if IS_WIN:
        import winreg
        path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path) as key:
                winreg.QueryValueEx(key, "LIFE OS")
            return True
        except OSError:
            return False
    return (Path.home() / ".config" / "autostart" / "lifeos.desktop").exists()


# ================================================================ процессы
@dataclass
class ProcInfo:
    pid: int
    name: str
    memory: int = 0           # байт
    cpu: str = ""
    user: str = ""


def list_processes(limit: int = 40) -> list[ProcInfo]:
    """Процессы, отсортированные по занятой памяти."""
    procs: list[ProcInfo] = []
    if IS_WIN:
        try:
            out = subprocess.run(
                ["tasklist", "/fo", "csv", "/nh"],
                capture_output=True, text=True, timeout=20,
                encoding="cp866", errors="ignore", **_no_window()).stdout
        except (OSError, subprocess.SubprocessError):
            return []
        import csv
        import io
        for row in csv.reader(io.StringIO(out)):
            if len(row) < 5:
                continue
            name, pid, _sess, _num, mem = row[:5]
            digits = "".join(c for c in mem if c.isdigit())
            try:
                procs.append(ProcInfo(pid=int(pid), name=name,
                                      memory=int(digits or 0) * 1024))
            except ValueError:
                continue
    else:
        try:
            out = subprocess.run(
                ["ps", "-eo", "pid,rss,comm", "--sort=-rss"],
                capture_output=True, text=True, timeout=20).stdout
        except (OSError, subprocess.SubprocessError):
            return []
        for line in out.splitlines()[1:]:
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            try:
                procs.append(ProcInfo(pid=int(parts[0]),
                                      memory=int(parts[1]) * 1024,
                                      name=parts[2]))
            except ValueError:
                continue
    procs.sort(key=lambda p: p.memory, reverse=True)
    return procs[:limit]


def kill_process(pid: int) -> tuple[bool, str]:
    """Завершает процесс по номеру."""
    try:
        if IS_WIN:
            r = subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                               capture_output=True, text=True, timeout=15,
                               **_no_window())
            if r.returncode == 0:
                return True, "Процесс завершён."
            return False, "Не удалось завершить: нужны права администратора."
        os.kill(pid, 9)
        return True, "Процесс завершён."
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"Ошибка: {exc}"


# ============================================================ анализ диска
@dataclass
class SizeNode:
    path: Path
    name: str
    size: int
    is_dir: bool


def scan_tree(root: Path, report=None, top: int = 25,
              cancelled=None) -> list[SizeNode]:
    """Самые объёмные папки и файлы внутри каталога.

    `cancelled` — функция без аргументов; если возвращает True, обход
    прекращается (окно закрыли, продолжать незачем).
    """
    nodes: list[SizeNode] = []
    try:
        entries = list(root.iterdir())
    except (PermissionError, OSError):
        return []
    for n, entry in enumerate(entries):
        if cancelled and cancelled():
            break
        if report and n % 3 == 0:
            report(int(n / max(1, len(entries)) * 100), f"Измеряем {entry.name}")
        try:
            if entry.is_symlink():
                continue
            if entry.is_file():
                nodes.append(SizeNode(entry, entry.name,
                                      entry.stat().st_size, False))
            elif entry.is_dir():
                total = 0
                for dp, _dn, fns in os.walk(entry, onerror=None):
                    if cancelled and cancelled():
                        break
                    for fn in fns:
                        try:
                            total += os.path.getsize(os.path.join(dp, fn))
                        except OSError:
                            continue
                nodes.append(SizeNode(entry, entry.name, total, True))
        except (PermissionError, OSError):
            continue
    nodes.sort(key=lambda x: x.size, reverse=True)
    return nodes[:top]


def find_large_files(roots: list[Path], min_size: int = 100 * 1024 * 1024,
                     report=None, limit: int = 60,
                     cancelled=None) -> list[SizeNode]:
    """Файлы крупнее заданного размера."""
    found: list[SizeNode] = []
    for n, root in enumerate(roots):
        if cancelled and cancelled():
            break
        if report:
            report(int(n / max(1, len(roots)) * 100), f"Поиск в {root.name}")
        for dirpath, dirnames, filenames in os.walk(root, onerror=None):
            if cancelled and cancelled():
                break
            dirnames[:] = [d for d in dirnames if not d.startswith(".")]
            for fn in filenames:
                fp = Path(dirpath) / fn
                try:
                    size = fp.stat().st_size
                except OSError:
                    continue
                if size >= min_size:
                    found.append(SizeNode(fp, fn, size, False))
            if len(found) > limit * 4:
                break
    found.sort(key=lambda x: x.size, reverse=True)
    return found[:limit]


# ========================================================== система и сеть
def system_info() -> list[tuple[str, str]]:
    """Основные сведения о компьютере."""
    rows: list[tuple[str, str]] = []
    rows.append(("Система", f"{platform.system()} {platform.release()}"))
    if IS_WIN:
        rows.append(("Версия", platform.version()))
    rows.append(("Имя компьютера", platform.node() or "—"))
    rows.append(("Процессор", platform.processor() or platform.machine()))
    rows.append(("Разрядность", platform.architecture()[0]))
    rows.append(("Ядер (логических)", str(os.cpu_count() or "—")))

    total = _total_memory()
    if total:
        rows.append(("Оперативная память", human_size(total)))
    try:
        u = shutil.disk_usage(str(Path.home()))
        rows.append(("Системный диск",
                     f"{human_size(u.total - u.used)} свободно из "
                     f"{human_size(u.total)}"))
    except OSError:
        pass
    rows.append(("Время работы", _uptime()))
    rows.append(("Python", platform.python_version()))
    return rows


def _total_memory() -> int:
    if IS_WIN:
        try:
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            st = MS()
            st.dwLength = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(st))
            return int(st.ullTotalPhys)
        except Exception:                                   # noqa: BLE001
            return 0
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (ValueError, OSError, AttributeError):
        return 0


def _uptime() -> str:
    seconds = 0
    if IS_WIN:
        try:
            import ctypes
            seconds = ctypes.windll.kernel32.GetTickCount64() / 1000
        except Exception:                                   # noqa: BLE001
            return "—"
    else:
        try:
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
        except OSError:
            return "—"
    days, rem = divmod(int(seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f"{days} дн. {hours} ч. {minutes} мин."
    if hours:
        return f"{hours} ч. {minutes} мин."
    return f"{minutes} мин."


def network_info() -> list[tuple[str, str]]:
    """Сведения о сети."""
    rows: list[tuple[str, str]] = []
    try:
        host = socket.gethostname()
        rows.append(("Имя в сети", host))
        rows.append(("Локальный адрес", _local_ip()))
    except OSError:
        pass
    ok, ms = _ping("8.8.8.8")
    rows.append(("Интернет", "Доступен" if ok else "Недоступен"))
    if ok:
        rows.append(("Отклик", f"{ms} мс"))
    rows.append(("DNS", "Работает" if _dns_ok() else "Не отвечает"))
    return rows


def _local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(1.0)
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "—"


def _dns_ok() -> bool:
    try:
        socket.setdefaulttimeout(3)
        socket.gethostbyname("github.com")
        return True
    except OSError:
        return False


def _ping(host: str) -> tuple[bool, int]:
    start = time.time()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((host, 53))
        return True, int((time.time() - start) * 1000)
    except OSError:
        return False, 0


# ================================================================ воркеры
@dataclass
class TableResult:
    """Универсальный результат: заголовки и строки."""
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    payload: list = field(default_factory=list)   # исходные объекты
    note: str = ""


class SystemWorker(QThread):
    """Фоновый сбор данных для инструментов анализа."""

    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, kind: str, parent=None):
        super().__init__(parent)
        self._kind = kind

    def run(self):
        try:
            result = self._collect()
        except Exception as exc:                            # noqa: BLE001
            if not self.isInterruptionRequested():
                self.failed.emit(str(exc))
            return
        if not self.isInterruptionRequested():
            self.done.emit(result)

    def _cancelled(self) -> bool:
        return self.isInterruptionRequested()

    def _collect(self) -> TableResult:
        kind = self._kind
        if kind == "startup":
            self.progress.emit(30, "Чтение списка автозагрузки…")
            items = list_startup()
            self.progress.emit(100, "Готово")
            return TableResult(
                headers=["Программа", "Откуда", "Команда"],
                rows=[[i.name, i.location, i.exe_path] for i in items],
                payload=items,
                note=("Отключайте только то, что знаете: часть записей "
                      "нужна драйверам и антивирусу.")
                if items else "Автозагрузка пуста.")

        if kind == "processes":
            self.progress.emit(30, "Опрос процессов…")
            procs = list_processes()
            self.progress.emit(100, "Готово")
            total = sum(p.memory for p in procs)
            return TableResult(
                headers=["Процесс", "Память", "PID"],
                rows=[[p.name, human_size(p.memory), str(p.pid)] for p in procs],
                payload=procs,
                note=(f"Показаны {len(procs)} самых требовательных · "
                      f"суммарно {human_size(total)}")
                if procs else "Не удалось получить список процессов.")

        if kind == "bigfiles":
            home = Path.home()
            roots = [p for p in (home / "Downloads", home / "Загрузки",
                                 home / "Documents", home / "Документы",
                                 home / "Videos", home / "Видео",
                                 home / "Desktop", home / "Рабочий стол")
                     if p.exists()] or [home]
            files = find_large_files(
                roots, report=lambda p, t: self.progress.emit(p, t),
                cancelled=self._cancelled)
            self.progress.emit(100, "Готово")
            return TableResult(
                headers=["Файл", "Размер", "Расположение"],
                rows=[[f.name, human_size(f.size), str(f.path.parent)]
                      for f in files],
                payload=files,
                note=(f"Файлы крупнее 100 МБ · всего "
                      f"{human_size(sum(f.size for f in files))}")
                if files else "Файлов крупнее 100 МБ не найдено.")

        if kind == "disktree":
            home = Path.home()
            nodes = scan_tree(home,
                              report=lambda p, t: self.progress.emit(p, t),
                              cancelled=self._cancelled)
            self.progress.emit(100, "Готово")
            return TableResult(
                headers=["Папка или файл", "Размер", "Тип"],
                rows=[[n.name, human_size(n.size),
                       "Папка" if n.is_dir else "Файл"] for n in nodes],
                payload=nodes,
                note=f"Содержимое {home} по убыванию размера"
                if nodes else "Не удалось прочитать домашнюю папку.")

        if kind == "sysinfo":
            self.progress.emit(50, "Опрос оборудования…")
            rows = system_info()
            self.progress.emit(100, "Готово")
            return TableResult(
                headers=["Параметр", "Значение"],
                rows=[[k, v] for k, v in rows],
                note="Сводка об этом компьютере")

        if kind == "network":
            self.progress.emit(40, "Проверка соединения…")
            rows = network_info()
            self.progress.emit(100, "Готово")
            online = any(k == "Интернет" and v == "Доступен"
                         for k, v in rows)
            return TableResult(
                headers=["Параметр", "Значение"],
                rows=[[k, v] for k, v in rows],
                note="Соединение в порядке" if online
                     else "Интернет недоступен — проверьте подключение")

        return TableResult(note="Неизвестный инструмент.")
