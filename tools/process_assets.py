"""
LIFE OS — обработка сырых изображений.

1) Вырезает зелёный хромакей (chroma key) из логотипов/иконок -> прозрачный PNG.
2) Режет спрайт-лист иконок 2x2 на 4 отдельные иконки.
3) Готовит производные размеры (256/128/64/32/16) и .ico для трея/окна.
4) Фоны просто копирует/ресайзит в 4K.

Запуск:  .venv/bin/python tools/process_assets.py
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "assets" / "raw"
OUT = ROOT / "assets"
(OUT / "logo").mkdir(parents=True, exist_ok=True)
(OUT / "icons").mkdir(parents=True, exist_ok=True)
(OUT / "backgrounds").mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------- chroma key
def chroma_key(img: Image.Image, tol: float = 0.34, despill: bool = True) -> Image.Image:
    """Убирает зелёный фон. Работает по «зеленоватости» пикселя."""
    img = img.convert("RGBA")
    a = np.asarray(img).astype(np.float32) / 255.0
    r, g, b, _ = a[..., 0], a[..., 1], a[..., 2], a[..., 3]

    # насколько зелёный доминирует над max(r, b)
    greenness = g - np.maximum(r, b)
    alpha = np.clip((tol - greenness) / max(tol * 0.55, 1e-5), 0.0, 1.0)

    # полностью прозрачное там, где явный хромакей
    alpha[greenness > tol] = 0.0

    if despill:
        # убираем зелёный ореол по краям
        spill = np.clip(g - (r + b) * 0.5, 0.0, 1.0)
        g = g - spill * 0.92
        r = r + spill * 0.10
        b = b + spill * 0.28

    rgb = np.clip(np.stack([r, g, b], axis=-1), 0.0, 1.0)
    out = np.concatenate([rgb, alpha[..., None]], axis=-1)
    res = Image.fromarray((out * 255.0).astype(np.uint8), "RGBA")

    # лёгкое сглаживание альфы, чтобы края не «пилили»
    rr, gg, bb, aa = res.split()
    aa = aa.filter(ImageFilter.GaussianBlur(0.7))
    return Image.merge("RGBA", (rr, gg, bb, aa))


def autocrop(img: Image.Image, pad_ratio: float = 0.03) -> Image.Image:
    """Обрезает по непрозрачному содержимому и делает квадрат с полями."""
    bbox = img.split()[-1].point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    side = int(max(w, h) * (1 + pad_ratio * 2))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def save_sizes(img: Image.Image, stem: str, folder: Path, sizes=(1024, 512, 256, 128, 64, 32)):
    folder.mkdir(parents=True, exist_ok=True)
    for s in sizes:
        img.resize((s, s), Image.LANCZOS).save(folder / f"{stem}_{s}.png")


def log(msg: str):
    print(f"  [assets] {msg}")


# ---------------------------------------------------------------- логотипы
def build_logos():
    jobs = [
        ("v2_logo_main.png", "logo", (2048, 1024, 512, 256, 128)),
        ("v2_logo_mini.png", "logo_mini", (512, 256, 128, 64)),
        ("v2_logo_tray.png", "logo_tray", (256, 128, 64, 32, 16)),
    ]
    for fname, stem, sizes in jobs:
        src = RAW / fname
        if not src.exists():
            log(f"пропуск {fname} (нет файла)")
            continue
        cut = autocrop(chroma_key(Image.open(src)))
        cut.save(OUT / "logo" / f"{stem}.png")
        save_sizes(cut, stem, OUT / "logo", sizes)
        log(f"{stem}: прозрачный PNG + {len(sizes)} размеров")

    # .ico для окна/трея/сборки
    ico_src = OUT / "logo" / "logo.png"
    if ico_src.exists():
        base = Image.open(ico_src)
        base.save(
            OUT / "logo" / "lifeos.ico",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )
        log("lifeos.ico собран")


# ---------------------------------------------------------------- иконки 2x2
ICON_NAMES = ["dashboard", "tools", "settings", "about"]


def build_icons():
    src = RAW / "icons_sheet_raw.png"
    if not src.exists():
        log("пропуск спрайт-листа иконок")
        return
    sheet = chroma_key(Image.open(src))
    w, h = sheet.size
    cells = [
        (0, 0, w // 2, h // 2),
        (w // 2, 0, w, h // 2),
        (0, h // 2, w // 2, h),
        (w // 2, h // 2, w, h),
    ]
    for name, box in zip(ICON_NAMES, cells):
        icon = autocrop(sheet.crop(box), pad_ratio=0.02)
        icon.save(OUT / "icons" / f"{name}.png")
        for s in (256, 128, 64, 48, 32):
            icon.resize((s, s), Image.LANCZOS).save(OUT / "icons" / f"{name}_{s}.png")
    log(f"иконки нарезаны: {', '.join(ICON_NAMES)}")


# ---------------------------------------------------------------- фоны
def build_backgrounds():
    jobs = [
        ("v2_bg_main.png", "bg_main", (3840, 2160)),
        ("v2_bg_violet.png", "bg_violet", (3840, 2160)),
        ("v2_splash.png", "splash", (1920, 1080)),
        ("v2_hero.png", "hero_card", (2400, 900)),
        ("v2_about.png", "about_art", (2048, 2048)),
    ]
    for fname, stem, target in jobs:
        src = RAW / fname
        if not src.exists():
            log(f"пропуск {fname}")
            continue
        img = Image.open(src).convert("RGB")
        # cover-ресайз без искажений
        tw, th = target
        sw, sh = img.size
        scale = max(tw / sw, th / sh)
        img = img.resize((max(1, int(sw * scale)), max(1, int(sh * scale))), Image.LANCZOS)
        left = (img.width - tw) // 2
        top = (img.height - th) // 2
        img = img.crop((left, top, left + tw, top + th))
        # JPEG q95: визуально идентично PNG, но в разы легче для репозитория
        img.save(OUT / "backgrounds" / f"{stem}.jpg", quality=95, subsampling=0, optimize=True)
        # лёгкая версия для быстрой отрисовки в UI
        img.resize((tw // 2, th // 2), Image.LANCZOS).save(
            OUT / "backgrounds" / f"{stem}@half.jpg", quality=92, optimize=True)
        log(f"{stem}: {tw}x{th}")


# --------------------------------------------- глиф-версии иконок (без плитки)
def build_glyph_icons():
    """Из стеклянных плиток делает чистые неоновые глифы с альфой по яркости.

    Нужно для мелких размеров (сайдбар, трей), где плитка превращается в кашу.
    """
    for name in ICON_NAMES:
        src = OUT / "icons" / f"{name}.png"
        if not src.exists():
            continue
        img = Image.open(src).convert("RGBA")
        w, h = img.size
        m = int(min(w, h) * 0.17)          # отрезаем рамку плитки
        img = img.crop((m, m, w - m, h - m))

        a = np.asarray(img).astype(np.float32) / 255.0
        rgb, alpha = a[..., :3], a[..., 3]
        lum = rgb.max(axis=-1)                       # яркость
        chroma = lum - rgb.min(axis=-1)              # насыщенность: неон цветной,
                                                     # а блик стекла серый
        signal = lum * np.clip(chroma / 0.22, 0.0, 1.0)
        mask = np.clip((signal - 0.14) / 0.40, 0.0, 1.0) ** 0.8
        new_alpha = mask * alpha

        # нормализуем цвет к чистому неону
        peak = np.maximum(rgb.max(axis=-1, keepdims=True), 1e-4)
        rgb = np.clip(rgb / peak, 0.0, 1.0)

        out = np.concatenate([rgb, new_alpha[..., None]], axis=-1)
        glyph = Image.fromarray((out * 255).astype(np.uint8), "RGBA")
        glyph = autocrop(glyph, pad_ratio=0.06)
        glyph.save(OUT / "icons" / f"{name}_glyph.png")
        for s in (256, 128, 64, 48, 32):
            glyph.resize((s, s), Image.LANCZOS).save(OUT / "icons" / f"{name}_glyph_{s}.png")
    log("глиф-иконки (прозрачные, без плитки) готовы")


if __name__ == "__main__":
    print("LIFE OS — сборка ассетов")
    build_logos()
    build_icons()
    build_glyph_icons()
    build_backgrounds()
    print("Готово.")
