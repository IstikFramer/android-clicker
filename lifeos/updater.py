"""LIFE OS — проверка и установка обновлений с GitHub.

Работа идёт в фоновом потоке, интерфейс не блокируется.

Порядок поиска новой версии:
  1. последний Release репозитория (если релизы опубликованы);
  2. файл data/version.json в ветке — на случай, когда релизов ещё нет.

Установка:
  скачивание архива -> распаковка во временную папку -> резервная копия
  текущей версии -> замена файлов -> перезапуск программы.
"""
from __future__ import annotations

import json
import os
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from . import config as cfg

GITHUB_OWNER = "IstikFramer"
GITHUB_REPO = "android-clicker"
GITHUB_BRANCH = "arena/01a0a388-android-clicker"

API_RELEASES = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
# Contents API отдаёт файл вместе с содержимым в base64 и, в отличие от
# raw.githubusercontent, доступен даже там, где raw-домен заблокирован.
API_CONTENTS = (f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
                f"/contents/data/version.json?ref={GITHUB_BRANCH}")
RAW_VERSION = (f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/"
               f"{GITHUB_BRANCH}/data/version.json")
BRANCH_ZIP = (f"https://codeload.github.com/{GITHUB_OWNER}/{GITHUB_REPO}/zip/refs/heads/"
              f"{GITHUB_BRANCH}")
BRANCH_PAGE = (f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/tree/{GITHUB_BRANCH}")
RELEASES_PAGE = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases"

USER_AGENT = f"LIFE-OS/{cfg.APP_VERSION}"
TIMEOUT = 15

# папки, которые никогда не трогаем при обновлении
PROTECTED = {".git", ".venv", "venv", "__pycache__", "backups"}


def normalize_changes(raw) -> dict[str, list[str]]:
    """Приводит список изменений к виду {"added": [...], ...}.

    Манифест может прийти в трёх формах: словарь групп, список словарей
    {"type", "text"} или простой список строк. Любая из них должна
    открываться, а не ронять окно обновления.
    """
    out: dict[str, list[str]] = {}
    if isinstance(raw, dict):
        for key, texts in raw.items():
            if isinstance(texts, (list, tuple)):
                out[str(key)] = [str(t) for t in texts]
            elif texts:
                out[str(key)] = [str(texts)]
    elif isinstance(raw, (list, tuple)):
        for item in raw:
            if isinstance(item, dict):
                out.setdefault(str(item.get("type", "added")), []).append(
                    str(item.get("text", "")))
            elif item:
                out.setdefault("added", []).append(str(item))
    return {k: [t for t in v if t] for k, v in out.items() if v}


def changes_from_notes(text: str) -> dict[str, list[str]]:
    """Вытаскивает списки из описания релиза GitHub (markdown)."""
    groups = {"added": "добав", "improved": "улучш", "fixed": "исправ"}
    out: dict[str, list[str]] = {}
    current = "added"
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        low = stripped.lower().lstrip("#* ").strip()
        matched = next((k for k, word in groups.items() if low.startswith(word)),
                       None)
        if matched and (stripped.startswith("#") or stripped.endswith(":")):
            current = matched
            continue
        if stripped[0] in "-*•":
            out.setdefault(current, []).append(stripped[1:].strip())
    return {k: v for k, v in out.items() if v}


# --------------------------------------------------------------------- версии
def parse_version(text: str) -> tuple:
    """'0.2.1-alpha' -> (0, 2, 1). Нечисловые хвосты отбрасываются."""
    core = str(text or "").strip().lstrip("vV").split("-")[0].split("+")[0]
    parts = []
    for chunk in core.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(remote: str, local: str = cfg.APP_VERSION) -> bool:
    return parse_version(remote) > parse_version(local)


@dataclass
class UpdateInfo:
    version: str = ""
    title: str = ""
    notes: str = ""
    changes: dict | list = field(default_factory=dict)
    url: str = ""            # ссылка на скачивание архива
    page: str = ""           # страница релиза для браузера
    size: int = 0
    published: str = ""
    source: str = ""         # release | branch
    available: bool = False


# ------------------------------------------------------------------ загрузка
def _open(url: str):
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    })
    ctx = ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx)


def _get_json(url: str) -> dict | None:
    try:
        with _open(url) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError):
        return None


def _get_version_file() -> dict | None:
    """Читает data/version.json из ветки: сначала через API, потом через raw."""
    data = _get_json(API_CONTENTS)
    if isinstance(data, dict) and data.get("content"):
        try:
            import base64
            raw = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(raw)
        except (ValueError, TypeError):
            pass
    data = _get_json(RAW_VERSION)
    return data if isinstance(data, dict) else None


def check_for_update() -> UpdateInfo:
    """Определяет, есть ли версия новее текущей."""
    # 1) релизы
    data = _get_json(API_RELEASES)
    if isinstance(data, dict) and data.get("tag_name"):
        version = str(data.get("tag_name", "")).lstrip("vV")
        asset_url, size = BRANCH_ZIP, 0
        for a in data.get("assets") or []:
            if str(a.get("name", "")).lower().endswith(".zip"):
                asset_url = a.get("browser_download_url") or asset_url
                size = int(a.get("size") or 0)
                break
        else:
            asset_url = data.get("zipball_url") or BRANCH_ZIP
        return UpdateInfo(
            version=version,
            title=data.get("name") or f"Версия {version}",
            notes=(data.get("body") or "").strip(),
            changes=changes_from_notes(data.get("body") or ""),
            url=asset_url,
            page=data.get("html_url") or RELEASES_PAGE,
            size=size,
            published=(data.get("published_at") or "")[:10],
            source="release",
            available=is_newer(version),
        )

    # 2) version.json в ветке
    data = _get_version_file()
    if isinstance(data, dict) and data.get("version"):
        version = str(data["version"])
        return UpdateInfo(
            version=version,
            title=data.get("title") or f"Версия {version}",
            notes=data.get("summary", ""),
            changes=normalize_changes(data.get("changes")),
            url=data.get("url") or BRANCH_ZIP,
            page=data.get("page") or BRANCH_PAGE,
            size=int(data.get("size") or 0),
            published=data.get("published") or data.get("date", ""),
            source="branch",
            available=is_newer(version),
        )
    return UpdateInfo()


# -------------------------------------------------------------------- потоки
class CheckWorker(QThread):
    """Фоновая проверка обновлений."""

    done = Signal(object)

    def run(self):
        try:
            self.done.emit(check_for_update())
        except Exception:
            self.done.emit(UpdateInfo())


class InstallWorker(QThread):
    """Скачивание, распаковка и установка обновления."""

    progress = Signal(int, str)     # проценты, подпись этапа
    finished_ok = Signal(str)       # путь к резервной копии
    failed = Signal(str)

    def __init__(self, info: UpdateInfo, parent=None):
        super().__init__(parent)
        self._info = info
        self._cancel = False

    def cancel(self):
        self._cancel = True

    # ------------------------------------------------------------ служебное
    # Архивы веток GitHub отдаются потоком без Content-Length, поэтому
    # точный процент неизвестен. В этом случае показываем оценку, которая
    # плавно приближается к 70 % и не выглядит зависшей.
    _ASSUMED_MB = 40.0

    def _download(self, url: str, dest: Path):
        with _open(url) as r:
            total = int(r.headers.get("Content-Length") or self._info.size or 0)
            got = 0
            last = -1
            with open(dest, "wb") as f:
                while True:
                    if self._cancel:
                        raise InterruptedError
                    chunk = r.read(64 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    got += len(chunk)
                    mb = got / 1048576
                    if total:
                        pct = min(70, int(got / total * 70))
                        text = f"Загрузка… {mb:.1f} из {total / 1048576:.1f} МБ"
                    else:
                        # асимптотика: чем больше скачано, тем ближе к 70
                        pct = int(70 * (1 - 0.5 ** (mb / self._ASSUMED_MB)))
                        text = f"Загрузка… {mb:.1f} МБ"
                    if pct != last:
                        last = pct
                        self.progress.emit(pct, text)

    @staticmethod
    def _unpack_root(tmp: Path) -> Path:
        """В архивах GitHub всё лежит внутри одной папки."""
        items = [p for p in tmp.iterdir() if p.is_dir()]
        return items[0] if len(items) == 1 else tmp

    @staticmethod
    def _prune_backups(keep: int = 3):
        """Оставляет только несколько последних резервных копий."""
        root = cfg.USER_DIR / "backups"
        if not root.exists():
            return
        items = sorted((p for p in root.iterdir() if p.is_dir()),
                       key=lambda p: p.stat().st_mtime, reverse=True)
        for old in items[keep:]:
            shutil.rmtree(old, ignore_errors=True)

    def _backup(self) -> Path:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dest = cfg.USER_DIR / "backups" / f"{cfg.APP_VERSION}-{stamp}"
        dest.mkdir(parents=True, exist_ok=True)
        for item in cfg.ROOT.iterdir():
            if item.name in PROTECTED:
                continue
            target = dest / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
        return dest

    @staticmethod
    def _find_exe(root: Path) -> Path | None:
        """Ищет .exe в распакованном архиве."""
        for cand in sorted(root.rglob("*.exe")):
            return cand
        return None

    @staticmethod
    def _stage_exe_swap(new_exe: Path) -> Path:
        """Готовит скрипт замены EXE и возвращает путь к нему."""
        current = Path(sys.executable).resolve()
        staged = cfg.USER_DIR / "update"
        staged.mkdir(parents=True, exist_ok=True)
        pending = staged / current.name
        shutil.copy2(new_exe, pending)

        backup = staged / f"{current.stem}-{cfg.APP_VERSION}.bak"
        script = staged / "apply_update.bat"
        # Ждём завершения программы, подменяем файл и запускаем заново.
        script.write_text(
            "@echo off\r\n"
            "chcp 65001 >nul\r\n"
            "echo Установка обновления LIFE OS...\r\n"
            ":wait\r\n"
            "timeout /t 1 /nobreak >nul\r\n"
            f'tasklist /fi "imagename eq {current.name}" | find /i "{current.name}" >nul '
            "&& goto wait\r\n"
            f'if exist "{backup}" del /q "{backup}"\r\n'
            f'move /y "{current}" "{backup}" >nul\r\n'
            f'move /y "{pending}" "{current}" >nul\r\n'
            f'start "" "{current}"\r\n'
            'del "%~f0"\r\n',
            encoding="utf-8")
        return script

    def _install(self, src: Path):
        for item in src.iterdir():
            if item.name in PROTECTED:
                continue
            target = cfg.ROOT / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

    # ------------------------------------------------------------------ run
    def run(self):
        tmpdir = None
        try:
            self.progress.emit(2, "Подключение к серверу…")
            tmpdir = Path(tempfile.mkdtemp(prefix="lifeos-update-"))
            archive = tmpdir / "update.zip"
            self._download(self._info.url, archive)

            if self._cancel:
                raise InterruptedError
            self.progress.emit(76, "Распаковка архива…")
            unpack = tmpdir / "unpacked"
            unpack.mkdir()
            with zipfile.ZipFile(archive) as z:
                z.extractall(unpack)
            root = self._unpack_root(unpack)

            # Собранный EXE обновляется подменой самого файла: Windows не
            # позволяет перезаписать запущенную программу, поэтому замену
            # выполняет маленький скрипт уже после её закрытия.
            if getattr(sys, "frozen", False):
                new_exe = self._find_exe(root)
                if new_exe is None:
                    raise FileNotFoundError(
                        "в архиве нет исполняемого файла программы")
                self.progress.emit(88, "Подготовка замены…")
                script = self._stage_exe_swap(new_exe)
                self.progress.emit(100, "Готово")
                self.finished_ok.emit(str(script))
                return

            if not (root / "main.py").exists():
                raise FileNotFoundError("в архиве не найден main.py")

            if self._cancel:
                raise InterruptedError
            self.progress.emit(84, "Резервная копия текущей версии…")
            backup = self._backup()

            self.progress.emit(92, "Установка файлов…")
            self._install(root)
            self._prune_backups()

            self.progress.emit(100, "Готово")
            self.finished_ok.emit(str(backup))
        except InterruptedError:
            self.failed.emit("Обновление отменено.")
        except urllib.error.URLError:
            self.failed.emit("Не удалось скачать файл: проверьте подключение к интернету.")
        except zipfile.BadZipFile:
            self.failed.emit("Загруженный архив повреждён.")
        except PermissionError:
            self.failed.emit("Нет прав на запись в папку программы.")
        except Exception as exc:
            self.failed.emit(f"Ошибка установки: {exc}")
        finally:
            if tmpdir and tmpdir.exists():
                shutil.rmtree(tmpdir, ignore_errors=True)


# ------------------------------------------------------------------ перезапуск
def restart_app(apply_script: str | None = None):
    """Перезапускает программу.

    Если передан путь к скрипту замены (режим собранного EXE), запускает
    его: скрипт дождётся закрытия программы, подменит файл и откроет
    новую версию.
    """
    try:
        if apply_script and Path(apply_script).exists():
            subprocess.Popen(
                ["cmd", "/c", "start", "", "/min", apply_script],
                cwd=str(Path(apply_script).parent),
                close_fds=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        elif getattr(sys, "frozen", False):
            subprocess.Popen([sys.executable], cwd=str(cfg.ROOT), close_fds=True)
        else:
            subprocess.Popen([sys.executable, str(cfg.ROOT / "main.py")],
                             cwd=str(cfg.ROOT), close_fds=True)
    except OSError:
        pass
    os._exit(0)
