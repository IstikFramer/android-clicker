# -*- mode: python ; coding: utf-8 -*-
"""Сборка LIFE OS в один исполняемый файл.

    pyinstaller lifeos.spec --noconfirm

Результат: dist/LIFE OS.exe — работает без установленного Python.
Ресурсы (иконки, фоны, данные) упаковываются внутрь файла.
"""
import sys
from pathlib import Path

ROOT = Path(SPECPATH)

# Внутрь EXE кладём только то, что нужно для работы: исходники изображений
# (assets/raw) и документация в поставку не попадают.
datas = [
    (str(ROOT / "assets" / "logo"), "assets/logo"),
    (str(ROOT / "assets" / "orbs"), "assets/orbs"),
    (str(ROOT / "assets" / "icons"), "assets/icons"),
    (str(ROOT / "assets" / "backgrounds"), "assets/backgrounds"),
    (str(ROOT / "data"), "data"),
]

# Иконка и метаданные версии подключаются, только если файлы на месте
# и платформа их поддерживает: иначе сборка продолжается без них.
_ico = ROOT / "assets" / "logo" / "lifeos.ico"
_icon = str(_ico) if _ico.exists() else None

_vi = ROOT / "tools" / "version_info.txt"
_version_file = str(_vi) if (_vi.exists() and sys.platform.startswith("win")) else None


a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["PySide6.QtSvg"],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "tkinter", "unittest", "pydoc_data", "numpy", "PIL",
        "PySide6.QtQml", "PySide6.QtQuick", "PySide6.Qt3DCore",
        "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
        "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
        "PySide6.QtBluetooth", "PySide6.QtPositioning", "PySide6.QtSql",
        "PySide6.QtTest", "PySide6.QtDesigner",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LIFE OS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # оконное приложение, без чёрной консоли
    disable_windowed_traceback=False,
    icon=_icon,
    version=_version_file,
)
