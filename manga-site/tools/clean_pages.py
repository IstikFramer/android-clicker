#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Убирает внешние поля страницы, на которых модель иногда рисует
английские подписи («PAGE 4» и т.п.): обрезает страницу до рамок панелей
плюс небольшой белый отступ.

Работает на ПОЛНОМ разрешении (тонкие рамки панелей при даунскейле
растворяются, из-за чего прошлая версия резала страницы по живому).
Предохранитель: с каждой стороны срезается не больше 12% высоты,
иначе страница остаётся нетронутой.

Запуск:  python3 tools/clean_pages.py [файл...]
Без аргументов — проходит по assets/img/train-742/ch1/*.jpg.
Скрипт идемпотентен: повторный запуск ничего не режет.
"""
import glob
import os
import sys

from PIL import Image

HERE = os.path.join(os.path.dirname(__file__), "..", "assets", "img", "train-742", "ch1")
MAX_CROP = 0.12  # максимум среза с одной стороны, доля высоты


def row_dark_fraction(px, y, w, x0, x1):
    dark = 0
    for x in range(x0, x1):
        if px[x, y] < 140:
            dark += 1
    return dark / (x1 - x0)


def find_border(px, w, h, from_top):
    """Первая строка (сверху или снизу), где начинается чёрная рамка панели:
    длинная горизонтальная тёмная линия."""
    rng = range(0, h) if from_top else range(h - 1, -1, -1)
    for y in rng:
        frac = row_dark_fraction(px, y, w, int(w * 0.08), int(w * 0.92))
        if frac > 0.55:
            return y
    return None


def clean(path):
    im = Image.open(path).convert("L")
    W, H = im.size
    px = im.load()

    top = find_border(px, W, H, True)
    bottom = find_border(px, W, H, False)
    if top is None or bottom is None or bottom <= top:
        print("skip (рамки не найдены):", os.path.basename(path))
        return False

    pad = 8
    y0 = max(0, top - pad)
    y1 = min(H, bottom + pad)
    cut_top = y0
    cut_bottom = H - y1

    if cut_top > MAX_CROP * H or cut_bottom > MAX_CROP * H:
        print("skip (подозрительно большой срез %d/%d): %s" % (cut_top, cut_bottom, os.path.basename(path)))
        return False

    if cut_top < 4 and cut_bottom < 4:
        print("ok   %s: полей с подписями нет" % os.path.basename(path))
        return False

    out = Image.open(path).crop((0, y0, W, y1))
    out.save(path, quality=92)
    print("crop %s: %dx%d -> %dx%d (top -%d, bottom -%d)" %
          (os.path.basename(path), W, H, out.size[0], out.size[1], cut_top, cut_bottom))
    return True


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(HERE, "*.jpg")))
    for f in files:
        clean(f)


if __name__ == "__main__":
    main()
