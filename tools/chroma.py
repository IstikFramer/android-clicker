#!/usr/bin/env python3
"""Remove green screen (#00FF00) from generated sprites -> PNG with alpha.

Usage: python3 chroma.py <src.png> <dst.png> <size> [--no-crop]
Also generates <size>/2 variant (small) when dst ends with _big pattern? No:
we call it twice per asset if needed.
"""
import sys
from PIL import Image

def remove_green(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            greenness = g - max(r, b)
            if g > 110 and greenness > 60:
                px[x, y] = (0, 0, 0, 0)
            elif g > 90 and greenness > 18:
                # feather edges (partial alpha)
                t = min(1.0, max(0.0, (greenness - 18) / 60.0))
                px[x, y] = (r, g, b, int(255 * (1 - t)))
    return im

def fit_square(im: Image.Image, size: str) -> Image.Image:
    if "x" in size:
        w, h = (int(v) for v in size.split("x"))
    else:
        w = h = int(size)
    im.thumbnail((w, h), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ox = (w - im.width) // 2
    oy = (h - im.height) // 2
    canvas.paste(im, (ox, oy), im)
    return canvas

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    no_crop = "--no-crop" in sys.argv[1:]
    src, dst, size = args[0], args[1], args[2]
    im = Image.open(src)
    im = remove_green(im)
    if not no_crop:
        bbox = im.getbbox()
        if bbox:
            im = im.crop(bbox)
    im = fit_square(im, size)
    im.save(dst, "PNG")
    print(f"saved {dst} {size}x{size}")

if __name__ == "__main__":
    main()
