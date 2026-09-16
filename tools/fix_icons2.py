#!/usr/bin/env python3
"""Pass 2 (fixed): always crop to the green-tile bbox inside the top square,
round corners with detected radius, normalize to 512x512 with transparent corners."""
import numpy as np
from pathlib import Path

from PIL import Image, ImageDraw

D = Path("/home/user/android-clicker/public/images/icons")


def main():
    for p in sorted(D.glob("*.png")):
        img = Image.open(p).convert("RGBA")
        w = min(img.size)
        sq = img.crop((0, 0, w, w))

        arr = np.asarray(sq.convert("RGB")).astype(int)
        r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
        mask = (g > 90) & (g > r + 30) & (g > b + 15)
        rowc, colc = mask.sum(axis=1), mask.sum(axis=0)
        rows = [y for y in range(w) if rowc[y] > 0.02 * w]
        cols = [x for x in range(w) if colc[x] > 0.02 * w]
        if not rows or not cols:
            print(f"SKIP {p.name}: no green")
            continue
        top, bot, left, right = rows[0], rows[-1], cols[0], cols[-1]
        tile = sq.crop((left, top, right + 1, bot + 1))
        tw, th = tile.size

        tmask = mask[top : bot + 1, left : right + 1]
        fx = next((x for x in range(tw) if tmask[0, x]), 0)
        fy = next((y for y in range(th) if tmask[y, 0]), 0)
        rad = max(fx, fy)
        if rad < 0.03 * min(tw, th):
            rad = 0.22 * min(tw, th)
        rad = min(max(rad, 0.12 * min(tw, th)), 0.28 * min(tw, th))

        alpha = Image.new("L", (tw, th), 0)
        ImageDraw.Draw(alpha).rounded_rectangle(
            [0, 0, tw - 1, th - 1], radius=int(rad), fill=255
        )
        tile.putalpha(alpha)
        tile = tile.resize((512, 512), Image.LANCZOS)
        tile.save(p)
        print(f"OK {p.name}: tile {tw}x{th}, radius={int(rad)} -> 512x512")


if __name__ == "__main__":
    main()
