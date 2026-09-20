#!/usr/bin/env python3
"""Procedurally draw remaining pixel-art assets in the same retro style."""
import math, random
from PIL import Image

def new_img(grid, cell):
    return Image.new("RGBA", (grid * cell, grid * cell), (0, 0, 0, 0)), cell

def put(im, cell, x, y, c):
    if c is None:
        return
    for dy in range(cell):
        for dx in range(cell):
            im.putpixel((x * cell + dx, y * cell + dy), c)

G = 16  # grid

# ---------------- COIN 32x32 ----------------
def draw_coin():
    im, cell = new_img(G, 2)
    c_out = (122, 74, 10, 255)
    c_dark = (196, 132, 20, 255)
    c_base = (255, 196, 40, 255)
    c_hi = (255, 240, 150, 255)
    cx = cy = 7.5
    for y in range(G):
        for x in range(G):
            d = math.hypot(x - cx, y - cy)
            if d <= 7.4:
                col = c_out
            elif d <= 6.4:
                col = c_dark if d > 5.6 else c_base
            else:
                col = None
            # highlight arc top-left
            if col == c_base and math.hypot(x - 5, y - 5) < 2.6:
                col = c_hi
            put(im, cell, x, y, col)
    # star engraving
    star = [(7,5),(6,6),(7,6),(8,6),(5,7),(6,7),(7,7),(8,7),(9,7),(6,8),(7,8),(8,8),(6,9),(8,9),(5,10),(9,10)]
    for (x, y) in star:
        put(im, cell, x, y, c_dark)
    im.save("assets/particles/part_coin.png")

# ---------------- SPARK 32x32 ----------------
def draw_spark():
    im, cell = new_img(G, 2)
    c_out = (200, 120, 0, 255)
    c_base = (255, 220, 60, 255)
    c_hi = (255, 255, 220, 255)
    for y in range(G):
        for x in range(G):
            dx, dy = abs(x - 7.5), abs(y - 7.5)
            r = max(dx, dy) + min(dx, dy) * 0.6
            if r <= 7.2:
                col = c_out
            elif r <= 6.2:
                col = c_hi if r < 1.8 else c_base
            else:
                col = None
            put(im, cell, x, y, col)
    im.save("assets/particles/part_spark.png")

# ---------------- HEART 32x32 ----------------
HEART = [
    "................",
    "..XXX....XXX....",
    ".XHHXX..XXXXX...",
    "XHHXXX..XXXXXX..",
    "XHHXXXXXXXXXXX..",
    "XXXXXXXXXXXXXX..",
    "XXXXXXXXXXXXXX..",
    ".XXXXXXXXXXXX...",
    "..XXXXXXXXXX....",
    "...XXXXXXXX.....",
    "....XXXXXX......",
    ".....XXXX.......",
    "......XX........",
    "................",
]
def draw_heart():
    im, cell = new_img(G, 2)
    base = (255, 90, 140, 255)
    dark = (160, 30, 80, 255)
    hi = (255, 200, 220, 255)
    for y, row in enumerate(HEART):
        for x, ch in enumerate(row):
            if ch == "X":
                put(im, cell, x, y, base)
            elif ch == "H":
                put(im, cell, x, y, hi)
    # outline: darken cells adjacent to empty
    px = im.load()
    w, h = im.size
    src = im.copy()
    sp = src.load()
    for y in range(h):
        for x in range(w):
            if sp[x, y][3] > 0:
                edge = False
                for ox, oy in ((2,0),(-2,0),(0,2),(0,-2)):
                    nx, ny = x+ox, y+oy
                    if nx < 0 or ny < 0 or nx >= w or ny >= h or sp[nx, ny][3] == 0:
                        edge = True
                if edge:
                    px[x, y] = dark
    im.save("assets/particles/part_heart.png")

# ---------------- ORCHARD TREE 64x64 ----------------
def draw_orchard():
    im, cell = new_img(G, 4)
    trunk = (122, 74, 30, 255)
    trunk_d = (90, 52, 20, 255)
    leaf = (60, 160, 70, 255)
    leaf_d = (40, 120, 50, 255)
    leaf_l = (100, 200, 100, 255)
    orng = (255, 150, 30, 255)
    orng_d = (210, 100, 10, 255)
    for y in range(G):
        for x in range(G):
            col = None
            # trunk
            if 11 <= y <= 15 and 7 <= x <= 8:
                col = trunk if x == 7 else trunk_d
            # crown: circle around (7.5, 5.5) r 5.4
            d = math.hypot((x - 7.5) * 1.0, (y - 5.5) * 1.25)
            if d <= 5.6:
                col = leaf
                if d > 4.6:
                    col = leaf_d
                elif (x + y * 3) % 5 == 0:
                    col = leaf_l
            put(im, cell, x, y, col)
    for (ox, oy) in [(4,4),(10,3),(7,7),(5,7),(11,6)]:
        put(im, cell, ox, oy, orng)
        put(im, cell, ox, oy + 1, orng_d) if oy + 1 < G else None
    im.save("assets/ui/icon_orchard.png")

# ---------------- GOLDEN LEAF 64x64 ----------------
def draw_leaf():
    im, cell = new_img(G, 4)
    out = (150, 90, 0, 255)
    base = (255, 200, 40, 255)
    hi = (255, 240, 150, 255)
    vein = (200, 130, 10, 255)
    for y in range(G):
        for x in range(G):
            t = y / 13.0
            half = 5.6 * math.sin(min(1.0, t) * math.pi) ** 0.8 if 0 < t < 1 else 0
            dx = abs(x - 7.5)
            if dx <= half + 0.6 and 1 <= y <= 14:
                if dx > half - 0.8:
                    col = out
                elif dx < 0.6:
                    col = vein
                elif x < 7.5 and y < 6:
                    col = hi
                else:
                    col = base
                put(im, cell, x, y, col)
    # stem
    put(im, cell, 7, 14, out)
    put(im, cell, 7, 15, out)
    # sparkle
    for (sx, sy) in [(11, 3), (12, 4), (11, 5), (10, 4)]:
        put(im, cell, sx, sy, (255, 255, 255, 255) if (sx, sy) == (11, 4) else hi)
    im.save("assets/ui/icon_leafgold.png")

# ---------------- BUTTONS 200x60 ----------------
def draw_button(path, top, base, bottom, outline, hi):
    W, H, cell = 200, 60, 4
    gw, gh = W // cell, H // cell
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    r = 3  # corner radius in cells
    for y in range(gh):
        for x in range(gw):
            # rounded mask
            cx = min(max(x, r), gw - 1 - r)
            cy = min(max(y, r), gh - 1 - r)
            if math.hypot(x - cx, y - cy) > r + 0.5:
                continue
            col = outline
            if 1 <= y <= gh - 2 and 1 <= x <= gw - 2:
                cxc = min(max(x, r), gw - 1 - r)
                cyc = min(max(y, r), gh - 2 - r)
                if math.hypot(x - cxc, y - cyc) > r - 0.5 + 1:
                    continue
                if y == 1 or (y == 2 and r > 0):
                    col = hi
                elif y <= gh // 3:
                    col = top
                elif y <= gh - 3:
                    col = base
                else:
                    col = bottom
            im.putpixel((x * cell, y * cell), col)
            for dy in range(cell):
                for dx in range(cell):
                    im.putpixel((x * cell + dx, y * cell + dy), col)
    im.save(path)

# ---------------- BACKGROUND 1080x1920 ----------------
def draw_bg():
    W, H, cell = 1080, 1920, 6
    gw, gh = W // cell, H // cell  # 180 x 320
    rnd = random.Random(42)
    im = Image.new("RGB", (W, H))
    def lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
    sky_top = (70, 160, 255)
    sky_bot = (170, 230, 255)
    horizon = int(gh * 0.62)
    for y in range(gh):
        if y < horizon + 24:
            col = lerp(sky_top, sky_bot, y / horizon)
        else:
            col = (0, 0, 0)
        for x in range(gw):
            im.putpixel((x * cell, y * cell), col)
            for dy in range(cell):
                for dx in range(cell):
                    im.putpixel((x * cell + dx, y * cell + dy), col)
    # sun
    sun = (255, 230, 100)
    sun_core = (255, 250, 190)
    for y in range(gh):
        for x in range(gw):
            d = math.hypot(x - gw * 0.78, y - gh * 0.10)
            if d < 14:
                c = sun_core if d < 9 else sun
                for dy in range(cell):
                    for dx in range(cell):
                        im.putpixel((x * cell + dx, y * cell + dy), c)
    # clouds
    for (ccx, ccy, s) in [(0.22, 0.14, 1.0), (0.55, 0.26, 0.8), (0.15, 0.38, 0.7), (0.8, 0.34, 0.9)]:
        for y in range(gh):
            for x in range(gw):
                dx = (x - gw * ccx) / (16 * s)
                dy = (y - gh * ccy) / (5 * s)
                if dx * dx + dy * dy < 1:
                    c = (255, 255, 255) if dy < 0.4 else (215, 235, 250)
                    for dyy in range(cell):
                        for dxx in range(cell):
                            im.putpixel((x * cell + dxx, y * cell + dyy), c)
    # hills
    hill1 = (70, 170, 90)
    hill2 = (50, 140, 70)
    for x in range(gw):
        h1 = horizon - int(6 * math.sin(x / 18.0) + 4 * math.sin(x / 7.0))
        h2 = horizon + 6 - int(5 * math.sin(x / 14.0 + 2))
        for y in range(h1, gh):
            c = hill1 if y < h2 else hill2
            for dy in range(cell):
                for dx in range(cell):
                    im.putpixel((x * cell + dx, y * cell + dy), c)
    # meadow
    meadow_top = horizon + 14
    grass1 = (90, 200, 100)
    grass2 = (70, 175, 85)
    for y in range(meadow_top, gh):
        for x in range(gw):
            n = rnd.random()
            c = grass1 if rnd.random() < 0.5 else grass2
            if n < 0.03:
                c = (110, 220, 120)
            for dy in range(cell):
                for dx in range(cell):
                    im.putpixel((x * cell + dx, y * cell + dy), c)
    # flowers
    for _ in range(60):
        x = rnd.randint(2, gw - 3)
        y = rnd.randint(meadow_top + 4, gh - 26)
        c = rnd.choice([(255, 255, 255), (255, 150, 200), (255, 220, 100)])
        for dy in range(cell):
            for dx in range(cell):
                im.putpixel((x * cell + dx, y * cell + dy), c)
    # pond at bottom
    pond_top = gh - 26
    water1 = (60, 140, 230)
    water2 = (40, 110, 200)
    shine = (140, 200, 250)
    for y in range(pond_top, gh):
        for x in range(gw):
            edge = int(10 * math.sin(x / 16.0) + 6 * math.sin(x / 6.0))
            if y > pond_top + 4 + edge:
                c = water1 if rnd.random() < 0.5 else water2
                if (x * 3 + y * 5) % 29 == 0:
                    c = shine
                for dy in range(cell):
                    for dx in range(cell):
                        im.putpixel((x * cell + dx, y * cell + dy), c)
    # side trees with oranges
    def tree(tx, ty, s):
        trunk = (110, 70, 30)
        leafc = (45, 130, 60)
        leafl = (70, 170, 80)
        orng = (255, 150, 30)
        for y in range(ty, ty + 14 * s):
            for x in range(tx - 2, tx + 2):
                if abs(x - tx) < 1.5:
                    for dy in range(cell):
                        for dx in range(cell):
                            im.putpixel((x * cell + dx, y * cell + dy), trunk)
        for y in range(ty - 16 * s, ty + 2):
            for x in range(tx - 12 * s, tx + 12 * s):
                d = math.hypot((x - tx) / (11 * s), (y - (ty - 8 * s)) / (9 * s))
                if d < 1:
                    c = leafl if d > 0.75 or ((x + y) % 6 == 0) else leafc
                    for dy in range(cell):
                        for dx in range(cell):
                            im.putpixel((x * cell + dx, y * cell + dy), c)
        for _ in range(7):
            ox = tx + rnd.randint(-8, 8)
            oy = ty - 8 * s + rnd.randint(-6, 6)
            for dy in range(cell):
                for dx in range(cell):
                    im.putpixel((ox * cell + dx, oy * cell + dy), orng)
    tree(16, int(gh * 0.66), 1)
    tree(gw - 16, int(gh * 0.68), 1)
    im.save("assets/backgrounds/bg_meadow.png")
    print("bg saved", im.size)

if __name__ == "__main__":
    import os
    os.makedirs("assets/particles", exist_ok=True)
    os.makedirs("assets/ui", exist_ok=True)
    os.makedirs("assets/backgrounds", exist_ok=True)
    draw_coin()
    draw_spark()
    draw_heart()
    draw_orchard()
    draw_leaf()
    draw_button("assets/ui/btn_orange.png", (255, 190, 80), (250, 140, 30), (200, 100, 15), (90, 45, 10), (255, 230, 160))
    draw_button("assets/ui/btn_blue.png", (120, 200, 255), (50, 140, 240), (25, 95, 190), (10, 40, 90), (200, 240, 255))
    draw_bg()
    print("done")
