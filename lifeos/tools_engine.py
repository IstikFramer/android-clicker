"""LIFE OS — движок инструментов обслуживания системы.

Каждый инструмент работает в две фазы: сначала СКАНИРОВАНИЕ (ничего не
меняем, только считаем), затем ОЧИСТКА — и только после явного согласия
пользователя. Ни один инструмент не удаляет файлы сам по себе.

Приоритет — Windows; на других системах инструмент сообщает, что недоступен,
но не падает.
"""
from __future__ import annotations

import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QThread, Signal

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"

# Возраст, начиная с которого файл в «Загрузках» считается старым.
OLD_DOWNLOAD_DAYS = 30
# Файлы меньше этого размера не участвуют в поиске дубликатов и крупных файлов.
MIN_DUPLICATE_SIZE = 1024 * 1024        # 1 МБ
# Ограничение обхода, чтобы сканирование не длилось вечно.
MAX_SCAN_FILES = 400_000


def human_size(num: float) -> str:
    """Человекочитаемый размер: 1.4 ГБ, 340 МБ, 12 КБ."""
    for unit, step in (("ТБ", 1024 ** 4), ("ГБ", 1024 ** 3),
                       ("МБ", 1024 ** 2), ("КБ", 1024)):
        if num >= step:
            return f"{num / step:.1f} {unit}".replace(".0 ", " ")
    return f"{int(num)} Б"


def human_count(n: int, forms: tuple[str, str, str]) -> str:
    """Склонение: 1 файл, 2 файла, 5 файлов."""
    n10, n100 = n % 10, n % 100
    if n10 == 1 and n100 != 11:
        return f"{n} {forms[0]}"
    if 2 <= n10 <= 4 and not 12 <= n100 <= 14:
        return f"{n} {forms[1]}"
    return f"{n} {forms[2]}"


# =========================================================== модель данных
@dataclass
class ScanItem:
    """Одна найденная группа файлов — строка в списке результатов."""
    key: str
    title: str
    detail: str
    size: int = 0
    count: int = 0
    paths: list[Path] = field(default_factory=list)
    checked: bool = True
    risky: bool = False          # требует особого внимания пользователя


@dataclass
class ScanResult:
    items: list[ScanItem] = field(default_factory=list)
    skipped: int = 0             # файлы, до которых не было доступа
    note: str = ""
    locked_paths: int = 0        # каталоги, требующие администратора

    @property
    def total_size(self) -> int:
        return sum(i.size for i in self.items)

    @property
    def total_count(self) -> int:
        return sum(i.count for i in self.items)

    @property
    def selected_size(self) -> int:
        return sum(i.size for i in self.items if i.checked)

    @property
    def selected_count(self) -> int:
        return sum(i.count for i in self.items if i.checked)


# ============================================================ общие утилиты
def _dir_stats(root: Path, skip_locked: bool = True) -> tuple[int, int, list[Path]]:
    """Суммарный размер, число файлов и список путей верхнего уровня."""
    total = size = 0
    tops: list[Path] = []
    if not root.exists():
        return 0, 0, []
    try:
        entries = list(root.iterdir())
    except (PermissionError, OSError):
        return 0, 0, []
    for entry in entries:
        try:
            if entry.is_symlink():
                continue
            if entry.is_file():
                size += entry.stat().st_size
                total += 1
                tops.append(entry)
            elif entry.is_dir():
                sub_size = sub_count = 0
                for dirpath, _dirnames, filenames in os.walk(entry, onerror=None):
                    for fn in filenames:
                        try:
                            sub_size += os.path.getsize(os.path.join(dirpath, fn))
                            sub_count += 1
                        except OSError:
                            if skip_locked:
                                continue
                    if sub_count > MAX_SCAN_FILES:
                        break
                size += sub_size
                total += sub_count
                tops.append(entry)
        except (PermissionError, OSError):
            continue
    return size, total, tops


def _try_unlink(path: Path) -> int:
    """Удаляет один файл. Возвращает освобождённый объём (0, если не вышло)."""
    try:
        size = path.stat().st_size
    except OSError:
        return 0
    try:
        path.unlink()
    except PermissionError:
        # Windows: снимаем «только чтение» и пробуем ещё раз.
        try:
            path.chmod(0o600)
            path.unlink()
        except OSError:
            return 0
    except OSError:
        return 0
    return size


def _delete(path: Path) -> tuple[int, int]:
    """Удаляет файл или каталог.

    Возвращает (освобождено байт, пропущено файлов). Считается только то,
    что действительно исчезло с диска: занятые процессами файлы Windows
    удалить нельзя, и записывать их в «освобождено» — обман.
    """
    freed = skipped = 0
    try:
        if path.is_symlink():
            try:
                path.unlink()
            except OSError:
                skipped += 1
            return freed, skipped
        if path.is_file():
            got = _try_unlink(path)
            return (got, 0) if got else (0, 1)
        if not path.is_dir():
            return 0, 0
    except OSError:
        return 0, 1

    # Каталог обходим снизу вверх и удаляем пофайлово, чтобы один
    # заблокированный файл не отменял очистку всей папки.
    for dirpath, dirnames, filenames in os.walk(path, topdown=False,
                                                onerror=None):
        for name in filenames:
            got = _try_unlink(Path(dirpath) / name)
            if got:
                freed += got
            else:
                skipped += 1
        for name in dirnames:
            try:
                (Path(dirpath) / name).rmdir()
            except OSError:
                pass
    try:
        path.rmdir()
    except OSError:
        pass
    return freed, skipped


# ============================================================= места поиска
def temp_dirs() -> list[Path]:
    out: list[Path] = []
    if IS_WIN:
        for env in ("TEMP", "TMP"):
            v = os.environ.get(env)
            if v:
                out.append(Path(v))
        win = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        out += [win / "Temp", win / "Prefetch"]
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        if local.name:
            out.append(local / "Microsoft" / "Windows" / "INetCache")
    else:
        out.append(Path(os.environ.get("TMPDIR", "/tmp")))
        out.append(Path.home() / ".cache")
    seen, res = set(), []
    for p in out:
        rp = str(p).lower()
        if p.exists() and rp not in seen:
            seen.add(rp)
            res.append(p)
    return res


def browser_cache_dirs() -> list[tuple[str, Path]]:
    res: list[tuple[str, Path]] = []
    home = Path.home()
    if IS_WIN:
        local = Path(os.environ.get("LOCALAPPDATA", str(home / "AppData/Local")))
        roaming = Path(os.environ.get("APPDATA", str(home / "AppData/Roaming")))
        cands = [
            ("Google Chrome", local / "Google/Chrome/User Data/Default/Cache"),
            ("Microsoft Edge", local / "Microsoft/Edge/User Data/Default/Cache"),
            ("Яндекс.Браузер", local / "Yandex/YandexBrowser/User Data/Default/Cache"),
            ("Opera", roaming / "Opera Software/Opera Stable/Cache"),
            ("Brave", local / "BraveSoftware/Brave-Browser/User Data/Default/Cache"),
        ]
        ff = roaming / "Mozilla/Firefox/Profiles"
        if ff.exists():
            for prof in ff.iterdir():
                if prof.is_dir():
                    cands.append(("Mozilla Firefox", prof / "cache2"))
    elif IS_MAC:
        c = home / "Library/Caches"
        cands = [("Google Chrome", c / "Google/Chrome/Default/Cache"),
                 ("Safari", c / "com.apple.Safari")]
    else:
        c = home / ".cache"
        cands = [("Google Chrome", c / "google-chrome/Default/Cache"),
                 ("Chromium", c / "chromium/Default/Cache"),
                 ("Mozilla Firefox", c / "mozilla/firefox")]
    for name, path in cands:
        if path.exists():
            res.append((name, path))
    return res


def recycle_bins() -> list[Path]:
    out: list[Path] = []
    if IS_WIN:
        import string
        for letter in string.ascii_uppercase:
            p = Path(f"{letter}:/$Recycle.Bin")
            if p.exists():
                out.append(p)
    else:
        for p in (Path.home() / ".local/share/Trash/files",
                  Path.home() / ".Trash"):
            if p.exists():
                out.append(p)
    return out


def downloads_dir() -> Path | None:
    for name in ("Downloads", "Загрузки"):
        p = Path.home() / name
        if p.exists():
            return p
    return None


def log_dirs() -> list[Path]:
    out: list[Path] = []
    if IS_WIN:
        win = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        out += [win / "Logs", win / "Minidump",
                win / "SoftwareDistribution" / "Download"]
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        if local.name:
            out.append(local / "CrashDumps")
    else:
        for p in (Path("/var/log"), Path.home() / ".local/state"):
            out.append(p)
    return [p for p in out if p.exists()]


def disk_usage() -> list[tuple[str, int, int]]:
    """Свободное место по дискам: (метка, занято, всего)."""
    out: list[tuple[str, int, int]] = []
    if IS_WIN:
        import string
        for letter in string.ascii_uppercase:
            root = f"{letter}:\\"
            if not os.path.exists(root):
                continue
            try:
                u = shutil.disk_usage(root)
            except OSError:
                continue
            out.append((f"Диск {letter}:", u.used, u.total))
    else:
        try:
            u = shutil.disk_usage(str(Path.home()))
            out.append(("Домашний раздел", u.used, u.total))
        except OSError:
            pass
    return out


# ============================================================= инструменты
class Tool:
    """Базовый инструмент: описание + сканирование + очистка."""

    key = ""
    name = ""
    subtitle = ""
    icon = "broom"
    action = "Очистить"
    windows_only = False
    hint = ""               # подробное пояснение для значка «?»

    def available(self) -> tuple[bool, str]:
        if self.windows_only and not IS_WIN:
            return False, "Инструмент доступен только в Windows."
        return True, ""

    def scan(self, report) -> ScanResult:      # pragma: no cover - интерфейс
        raise NotImplementedError

    def clean(self, items: list[ScanItem], report) -> tuple[int, int]:
        """Удаляет выбранное.

        Возвращает (освобождено байт, пропущено файлов). Пропуски — это
        файлы, занятые работающими программами: они остаются на месте.
        """
        freed = skipped = 0
        total = sum(len(i.paths) for i in items) or 1
        done = 0
        for item in items:
            for path in item.paths:
                got, miss = _delete(path)
                freed += got
                skipped += miss
                done += 1
                if done % 10 == 0 or done == total:
                    report(int(done / total * 100), f"Удаление… {item.title}")
        return freed, skipped


class TempTool(Tool):
    hint = ("Временные файлы создают установщики и программы во время работы. После"
            " завершения они обычно не нужны, но остаются на диске и со временем занимают гигабайты. Удаление безопасно: файлы, занятые работающими программами, пропускаются.")
    key, icon = "temp", "broom"
    name = "Временные файлы"
    subtitle = "Мусор, оставшийся от установщиков и программ"

    def scan(self, report) -> ScanResult:
        res = ScanResult()
        dirs = temp_dirs()
        for n, root in enumerate(dirs):
            report(int(n / max(1, len(dirs)) * 100), f"Проверка {root}")
            size, count, tops = _dir_stats(root)
            if not os.access(root, os.W_OK):
                res.locked_paths += 1
            if count:
                res.items.append(ScanItem(
                    key=str(root), title=root.name or str(root),
                    detail=str(root), size=size, count=count, paths=tops))
        if not res.items:
            res.note = "Временных файлов не найдено — система уже чистая."
        return res


class RecycleTool(Tool):
    hint = ("Удалённые файлы попадают в Корзину и продолжают занимать место на диск"
            "е до её очистки. После очистки восстановить их штатными средствами не получится — проверьте содержимое заранее.")
    key, icon = "recycle", "trash"
    name = "Корзина"
    subtitle = "Удалённые файлы, всё ещё занимающие место"
    action = "Очистить корзину"

    def scan(self, report) -> ScanResult:
        res = ScanResult()
        bins = recycle_bins()
        for n, root in enumerate(bins):
            report(int(n / max(1, len(bins)) * 100), f"Проверка {root}")
            size, count, tops = _dir_stats(root)
            if count:
                disk = str(root)[:2] if IS_WIN else "Корзина"
                res.items.append(ScanItem(
                    key=str(root), title=f"Корзина {disk}", detail=str(root),
                    size=size, count=count, paths=tops))
        if not res.items:
            res.note = "Корзина пуста."
        return res


class BrowserCacheTool(Tool):
    hint = ("Браузеры сохраняют картинки и страницы, чтобы сайты открывались быстре"
            "е. Кэш может вырасти до нескольких гигабайт. Удаление не затрагивает пароли, закладки и историю: сайты просто загрузятся чуть медленнее в первый раз.")
    key, icon = "browser", "globe"
    name = "Кэш браузеров"
    subtitle = "Временные страницы и картинки Chrome, Edge, Firefox и других"

    def scan(self, report) -> ScanResult:
        res = ScanResult()
        found = browser_cache_dirs()
        for n, (label, root) in enumerate(found):
            report(int(n / max(1, len(found)) * 100), f"Проверка {label}")
            size, count, tops = _dir_stats(root)
            if count:
                res.items.append(ScanItem(
                    key=str(root), title=label, detail=str(root),
                    size=size, count=count, paths=tops))
        if not res.items:
            res.note = "Кэш браузеров пуст или браузеры не установлены."
        return res


class DownloadsTool(Tool):
    hint = ("Показывает файлы из папки «Загрузки», которые не открывались больше 30"
            " дней. Это ваши личные файлы, поэтому по умолчанию ничего не отмечено — выберите вручную то, что не нужно.")
    key, icon = "downloads", "folder"
    name = "Старые загрузки"
    subtitle = f"Файлы из папки «Загрузки» старше {OLD_DOWNLOAD_DAYS} дней"
    action = "Удалить выбранное"

    def scan(self, report) -> ScanResult:
        res = ScanResult()
        root = downloads_dir()
        if root is None:
            res.note = "Папка «Загрузки» не найдена."
            return res
        cutoff = time.time() - OLD_DOWNLOAD_DAYS * 86400
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
        except (PermissionError, OSError):
            res.note = "Нет доступа к папке «Загрузки»."
            return res
        for n, entry in enumerate(entries):
            if n % 25 == 0:
                report(int(n / max(1, len(entries)) * 100), "Проверка загрузок")
            try:
                st = entry.stat()
            except OSError:
                res.skipped += 1
                continue
            if st.st_mtime > cutoff:
                continue
            if entry.is_dir():
                size, count, _ = _dir_stats(entry)
            else:
                size, count = st.st_size, 1
            if not count:
                continue
            days = int((time.time() - st.st_mtime) / 86400)
            res.items.append(ScanItem(
                key=str(entry), title=entry.name,
                detail=f"{human_size(size)} · не открывался {days} дн.",
                size=size, count=count, paths=[entry],
                checked=False, risky=True))
        res.items.sort(key=lambda i: i.size, reverse=True)
        if not res.items:
            res.note = "Старых загрузок нет."
        else:
            res.note = ("Это ваши личные файлы — отметьте только то, "
                        "что действительно не нужно.")
        return res


class LogsTool(Tool):
    hint = ("Журналы работы Windows, дампы памяти после сбоев и остатки установленн"
            "ых обновлений. Нужны в основном для диагностики неполадок; если проблем нет, их можно удалить.")
    key, icon = "logs", "logfile"
    name = "Журналы и отчёты об ошибках"
    subtitle = "Логи Windows, дампы памяти и остатки обновлений"
    windows_only = False

    def scan(self, report) -> ScanResult:
        res = ScanResult()
        dirs = log_dirs()
        for n, root in enumerate(dirs):
            report(int(n / max(1, len(dirs)) * 100), f"Проверка {root.name}")
            size, count, tops = _dir_stats(root)
            if not os.access(root, os.W_OK):
                res.locked_paths += 1
            if count:
                res.items.append(ScanItem(
                    key=str(root), title=root.name, detail=str(root),
                    size=size, count=count, paths=tops,
                    checked=root.name != "Logs", risky=True))
        if not res.items:
            res.note = "Журналов не найдено."
        else:
            res.note = "Журналы могут пригодиться при диагностике проблем."
        return res


class DuplicatesTool(Tool):
    hint = ("Ищет одинаковые файлы крупнее 1 МБ в ваших документах, картинках и заг"
            "рузках. Сравнивается содержимое, а не имя. Самая старая копия каждого файла всегда остаётся на месте.")
    key, icon = "duplicates", "duplicate"
    name = "Дубликаты файлов"
    subtitle = "Одинаковые копии в документах, картинках и загрузках"
    action = "Удалить копии"

    def _roots(self) -> list[Path]:
        home = Path.home()
        names = ("Documents", "Документы", "Downloads", "Загрузки",
                 "Pictures", "Изображения", "Videos", "Видео",
                 "Music", "Музыка", "Desktop", "Рабочий стол")
        out = [home / n for n in names]
        return [p for p in out if p.exists()]

    def scan(self, report) -> ScanResult:
        import hashlib
        res = ScanResult()
        by_size: dict[int, list[Path]] = {}
        roots = self._roots()
        seen = 0
        for n, root in enumerate(roots):
            report(int(n / max(1, len(roots)) * 60), f"Обход {root.name}")
            for dirpath, dirnames, filenames in os.walk(root, onerror=None):
                dirnames[:] = [d for d in dirnames if not d.startswith(".")]
                for fn in filenames:
                    fp = Path(dirpath) / fn
                    try:
                        sz = fp.stat().st_size
                    except OSError:
                        continue
                    if sz < MIN_DUPLICATE_SIZE:
                        continue
                    by_size.setdefault(sz, []).append(fp)
                    seen += 1
                    if seen > MAX_SCAN_FILES:
                        break

        cands = {s: ps for s, ps in by_size.items() if len(ps) > 1}
        total = max(1, len(cands))
        for n, (sz, paths) in enumerate(cands.items()):
            report(60 + int(n / total * 40), "Сверка содержимого")
            by_hash: dict[str, list[Path]] = {}
            for fp in paths:
                try:
                    h = hashlib.blake2b(digest_size=16)
                    with open(fp, "rb") as f:
                        h.update(f.read(262144))
                        f.seek(max(0, sz - 262144))
                        h.update(f.read(262144))
                    by_hash.setdefault(h.hexdigest(), []).append(fp)
                except OSError:
                    res.skipped += 1
            for group in by_hash.values():
                if len(group) < 2:
                    continue
                group.sort(key=lambda p: p.stat().st_mtime)
                extra = group[1:]          # оригинал (самый старый) сохраняем
                res.items.append(ScanItem(
                    key=str(group[0]), title=group[0].name,
                    detail=(f"{len(group)} копии · оставим "
                            f"{group[0].parent}"),
                    size=sz * len(extra), count=len(extra), paths=extra,
                    checked=True, risky=True))
        res.items.sort(key=lambda i: i.size, reverse=True)
        if not res.items:
            res.note = "Дубликатов крупнее 1 МБ не найдено."
        else:
            res.note = "Самая старая копия каждого файла останется на месте."
        return res


ALL_TOOLS: list[Tool] = [
    TempTool(), RecycleTool(), BrowserCacheTool(),
    DownloadsTool(), LogsTool(), DuplicatesTool(),
]


def tool_by_key(key: str) -> Tool | None:
    return next((t for t in ALL_TOOLS if t.key == key), None)


# ================================================================ воркеры
class ScanWorker(QThread):
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str)

    def __init__(self, tool: Tool, parent=None):
        super().__init__(parent)
        self._tool = tool

    def run(self):
        try:
            res = self._tool.scan(
                lambda p, t: self.progress.emit(max(0, min(100, p)), t))
            self.done.emit(res)
        except Exception as exc:                    # noqa: BLE001
            self.failed.emit(str(exc))


class CleanWorker(QThread):
    progress = Signal(int, str)
    done = Signal(int, int)          # освобождено байт, пропущено файлов
    failed = Signal(str)

    def __init__(self, tool: Tool, items: list[ScanItem], parent=None):
        super().__init__(parent)
        self._tool = tool
        self._items = items

    def run(self):
        try:
            freed, skipped = self._tool.clean(
                self._items,
                lambda p, t: self.progress.emit(max(0, min(100, p)), t))
            self.done.emit(freed, skipped)
        except Exception as exc:                    # noqa: BLE001
            self.failed.emit(str(exc))
