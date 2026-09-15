#!/usr/bin/env python3
"""Сборка релизного архива LIFE OS без исходных материалов.

Из архива исключаются assets/raw (исходники для генерации), docs, .git и
прочее, что не нужно для запуска: вес обновления падает примерно втрое.

    python tools/make_release.py            # dist/lifeos-<версия>.zip
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lifeos import config as cfg  # noqa: E402

# Каталоги, которые не попадают в обновление.
EXCLUDE_DIRS = {
    ".git", ".github", ".venv", "venv", "__pycache__", "dist",
    "docs", ".idea", ".vscode", ".pytest_cache", ".ruff_cache",
}
EXCLUDE_REL = {Path("assets/raw")}
EXCLUDE_SUFFIX = {".pyc", ".pyo", ".log", ".zip"}


def included(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDE_DIRS for part in rel.parts):
        return False
    if any(rel == e or e in rel.parents for e in EXCLUDE_REL):
        return False
    return path.suffix.lower() not in EXCLUDE_SUFFIX


def main() -> int:
    out_dir = ROOT / "dist"
    out_dir.mkdir(exist_ok=True)
    out = out_dir / f"lifeos-{cfg.APP_VERSION}.zip"
    files = [p for p in ROOT.rglob("*") if p.is_file() and included(p)]
    total = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in files:
            z.write(p, Path(f"lifeos-{cfg.APP_VERSION}") / p.relative_to(ROOT))
            total += p.stat().st_size
    size = out.stat().st_size
    print(f"  {out.relative_to(ROOT)}")
    print(f"  файлов: {len(files)} · исходно {total / 1048576:.1f} МБ "
          f"· в архиве {size / 1048576:.1f} МБ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
