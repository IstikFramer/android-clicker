"""LIFE OS — работа с правами администратора Windows.

Часть системного мусора (Windows\\Temp, Prefetch, дампы памяти, Корзина
других учётных записей) недоступна обычному пользователю. Программа не
требует администратора при запуске: она сообщает, когда он нужен, и
перезапускается по кнопке через штатный запрос UAC.
"""
from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

IS_WIN = sys.platform.startswith("win")


def is_admin() -> bool:
    """Запущена ли программа с правами администратора."""
    if not IS_WIN:
        try:
            return os.geteuid() == 0
        except AttributeError:
            return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:                                   # noqa: BLE001
        return False


def can_elevate() -> bool:
    """Доступен ли перезапуск с повышением прав."""
    return IS_WIN and not is_admin()


def _launch_args() -> tuple[str, str]:
    """Возвращает (исполняемый файл, аргументы) для перезапуска."""
    if getattr(sys, "frozen", False):
        # Собранный EXE: перезапускаем сам файл.
        return sys.executable, " ".join(f'"{a}"' for a in sys.argv[1:])
    script = Path(sys.argv[0]).resolve()
    args = " ".join([f'"{script}"'] + [f'"{a}"' for a in sys.argv[1:]])
    return sys.executable, args


def relaunch_as_admin() -> bool:
    """Перезапускает программу через UAC.

    Возвращает True, если запрос принят и текущий процесс должен закрыться.
    Если пользователь нажал «Нет» в окне UAC — возвращает False.
    """
    if not IS_WIN or is_admin():
        return False
    exe, args = _launch_args()
    try:
        # ShellExecuteW с глаголом "runas" показывает стандартный запрос UAC.
        rc = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", exe, args, str(Path.cwd()), 1)
    except Exception:                                   # noqa: BLE001
        return False
    # Значения больше 32 означают успешный запуск.
    return int(rc) > 32


def needs_admin_paths() -> list[str]:
    """Каталоги очистки, которые обычно требуют администратора."""
    if not IS_WIN:
        return []
    win = os.environ.get("SystemRoot", r"C:\Windows")
    return [
        f"{win}\\Temp",
        f"{win}\\Prefetch",
        f"{win}\\Logs",
        f"{win}\\Minidump",
        f"{win}\\SoftwareDistribution\\Download",
    ]


def probe_locked(paths: list[Path]) -> int:
    """Считает, к скольким путям нет доступа на запись."""
    blocked = 0
    for p in paths:
        try:
            if p.exists() and not os.access(p, os.W_OK):
                blocked += 1
        except OSError:
            blocked += 1
    return blocked
