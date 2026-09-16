#!/usr/bin/env python3
"""Unify generated icon set: crop to the green tile, make corners transparent."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
ICONS_DIR = ROOT / "public" / "images" / "icons"


def green_mask(img: Image.Image):
    """Boolean-ish mask: pixel counts as green if G dominates R and B."""
    r, g, b = img.split()[:3]
    # build via point ops: keep pixel where G>90 and G-R>30 and G-B>15
    import numpy as np
    arr = np.stack([np.asarray(r), np.asarray(g), np.asarray(b)], axis=-1)
    mask = (arr[..., 1] > 90) & (arr[..., 1] > arr[..., 0] + 30) & (arr[..., 1] > arr[..., 2] + 15)
    return mask


def main():
    for p in sorted(ICONS_DIR.glob("*.png")):
        img = Image.open(p).convert("RGB")
        w, h = img.size
        mask = green_mask(img)

        # rows/cols that meaningfully contain green
        row_cnt = mask.sum(axis=1)
        col_cnt = mask.sum(axis=0)
        rows = [y for y in range(h) if row_cnt[y] > 0.02 * w]
        cols = [x for x in range(w) if col_cnt[x] > 0.02 * h]
        if not rows or not cols:
            print(f"SKIP {p.name}: no green region")
            continue
        top, bottom, left, right = rows[0], rows[-1], cols[0], cols[-1]
        bw, bh = right - left + 1, bottom - top + 1

        full_bleed = (bw / w) > 0.88 and (bh / h) > 0.88
        crop = img.crop((left, top, left + bw, bottom + bh))
        cw, ch = crop.size

        # estimate corner radius from the cropped tile
        cmask = mask[top : top + bh, left : left + bw]
        first_x = next((x for x in range(cw) if cmask[0, x]), 0)
        first_y = next((y for y in range(ch) if cmask[y, 0]), 0)
        r = max(first_x, first_y)
        if full_bleed or r < 0.03 * min(cw, ch):
            r = 0.22 * min(cw, ch)  # unified app-icon rounding
        r = int(min(max(r, 0.12 * min(cw, ch)), 0.28 * min(cw, ch)))

        # rounded-corner alpha mask
        alpha = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(alpha).rounded_rectangle([0, 0, cw - 1, ch - 1], radius=r, fill=255)
        out = crop.convert("RGBA")
        out.putalpha(alpha)
        out.save(p)
        kind = "full-bleed" if full_bleed else "cropped tile"
        print(f"OK {p.name}: {kind}, {img.size}->{out.size}, radius={r}")


if __name__ == "__main__":
    main()
