#!/usr/bin/env python3
"""Remove green screen (#00FF00) -> PNG with alpha.

Only greens CONNECTED to the image border are removed (flood fill),
so interior greens (leaves, gems) survive. Feathered edges.
Usage: python3 chroma.py <src.png> <dst.png> <size|WxH> [--no-crop]
"""
import sys
from collections import deque
from PIL import Image

def is_bg(r, g, b):
    return g > 110 and (g - max(r, b)) > 60

def is_edge(r, g, b):
    return g > 90 and (g - max(r, b)) > 18

def remove_green(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    px = im.load()
    keep = bytearray(w * h)  # 1 = foreground
    # seed flood fill from borders through bg-green pixels
    q = deque()
    seen = bytearray(w * h)
    def seed(x, y):
        if 0 <= x < w and 0 <= y < h and not seen[y * w + x]:
            r, g, b, a = px[x, y]
            if is_bg(r, g, b):
                seen[y * w + x] = 1
                q.append((x, y))
    for x in range(w):
        seed(x, 0); seed(x, h - 1)
    for y in range(h):
        seed(0, y); seed(w - 1, y)
    while q:
        x, y = q.popleft()
        for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx]:
                r, g, b, a = px[nx, ny]
                if is_bg(r, g, b):
                    seen[ny * w + nx] = 1
                    q.append((nx, ny))
    # apply: connected bg -> transparent; edge-adjacent -> feather
    for y in range(h):
        for x in range(w):
            if seen[y * w + x]:
                px[x, y] = (0, 0, 0, 0)
            else:
                r, g, b, a = px[x, y]
                if is_edge(r, g, b):
                    # feather only if touching removed bg
                    touch = False
                    for nx, ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                        if 0 <= nx < w and 0 <= ny < h and seen[ny * w + nx]:
                            touch = True; break
                    if touch:
                        t = min(1.0, max(0.0, ((g - max(r, b)) - 18) / 60.0))
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
    print(f"saved {dst} {size}")

if __name__ == "__main__":
    main()
